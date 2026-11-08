"""Hugging Face Datasets および GitHub Releases 向け法令データセット生成・配信モジュール."""

from __future__ import annotations

import io
import json
import logging
import re
import tarfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 日本の主要基本法令（Core Laws）の法令IDおよび通称一覧
CORE_LAWS: dict[str, str] = {
    "321CONSTITUTION": "日本国憲法",
    "129AC0000000089": "民法",
    "140AC0000000045": "刑法",
    "132AC0000000048": "商法",
    "417AC0000000086": "会社法",
    "323AC0000000131": "刑事訴訟法",
    "408AC0000000109": "民事訴訟法",
    "322AC0000000049": "労働基準法",
    "405AC0000000088": "行政手続法",
    "415AC0000000057": "個人情報の保護に関する法律",
    "503AC0000000035": "デジタル社会形成基本法",
    "345AC0000000048": "著作権法",
    "334AC0000000121": "特許法",
    "322AC0000000054": "私的独占の禁止及び公正取引の確保に関する件",
}


@dataclass
class LawArticleRecord:
    """Parquet出力用の1条文レコード."""

    law_id: str
    law_num: str
    law_title: str
    article_num: str
    hierarchy_path: str
    title: str
    content: str
    outbound_references: list[str]
    inbound_references: list[str]
    defined_terms: list[str]
    child_anchors_json: str


def download_law_xml(law_id: str, output_path: Path) -> Path:
    """e-Gov 法令APIから法令XMLを取得して保存する."""
    url = f"https://elaws.e-gov.go.jp/api/1/lawdata/{law_id}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "law2markdown-dataset-builder/0.1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        if res.status != 200:
            raise RuntimeError(f"Failed to download law {law_id}: HTTP {res.status}")
        data = res.read()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    return output_path


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """MarkdownからYAML Frontmatterと本文を分離する."""
    match = re.match(r"^---\n(.*?)\n---\n*(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    fm_raw = match.group(1)
    body = match.group(2)

    try:
        import yaml

        meta = yaml.safe_load(fm_raw)
        return (meta if isinstance(meta, dict) else {}), body
    except Exception:
        # Fallback naive parser
        meta: dict[str, Any] = {}
        for line in fm_raw.splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip("\"'")
        return meta, body


def collect_article_records(kb_dir: Path) -> list[LawArticleRecord]:
    """生成済ナレッジベースから条文データを収集する."""
    records: list[LawArticleRecord] = []

    for article_file in kb_dir.glob("**/articles/*.md"):
        text = article_file.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        child_anchors = meta.get("child_anchors", [])
        child_anchors_json = (
            json.dumps(child_anchors, ensure_ascii=False) if child_anchors else "[]"
        )

        records.append(
            LawArticleRecord(
                law_id=str(meta.get("law_id", "")),
                law_num=str(meta.get("law_num", "")),
                law_title=str(meta.get("title", "")).split(" ")[0],
                article_num=str(meta.get("article_num", "")),
                hierarchy_path=str(meta.get("hierarchy_path", "")),
                title=str(meta.get("title", "")),
                content=body,
                outbound_references=meta.get("outbound_references", []),
                inbound_references=meta.get("inbound_references", []),
                defined_terms=meta.get("defined_terms", []),
                child_anchors_json=child_anchors_json,
            )
        )
    return records


def export_articles_parquet(records: list[LawArticleRecord], output_parquet_path: Path) -> Path:
    """条文レコード群をPyArrowを用いてParquet形式で保存する."""
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as e:
        raise ImportError("pyarrow がインストールされていません: uv pip install pyarrow") from e

    data = {
        "law_id": [r.law_id for r in records],
        "law_num": [r.law_num for r in records],
        "law_title": [r.law_title for r in records],
        "article_num": [r.article_num for r in records],
        "hierarchy_path": [r.hierarchy_path for r in records],
        "title": [r.title for r in records],
        "content": [r.content for r in records],
        "outbound_references": [r.outbound_references for r in records],
        "inbound_references": [r.inbound_references for r in records],
        "defined_terms": [r.defined_terms for r in records],
        "child_anchors_json": [r.child_anchors_json for r in records],
    }

    schema = pa.schema(
        [
            ("law_id", pa.string()),
            ("law_num", pa.string()),
            ("law_title", pa.string()),
            ("article_num", pa.string()),
            ("hierarchy_path", pa.string()),
            ("title", pa.string()),
            ("content", pa.string()),
            ("outbound_references", pa.list_(pa.string())),
            ("inbound_references", pa.list_(pa.string())),
            ("defined_terms", pa.list_(pa.string())),
            ("child_anchors_json", pa.string()),
        ]
    )

    table = pa.Table.from_pydict(data, schema=schema)
    output_parquet_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output_parquet_path, compression="zstd")
    return output_parquet_path


def create_markdown_tar_zst(source_dir: Path, output_archive_path: Path) -> Path:
    """Markdownナレッジベースをtarアーカイブとして保存する."""
    output_archive_path.parent.mkdir(parents=True, exist_ok=True)
    # zstandardが利用可能ならzstd圧縮、なければgzip fallback
    try:
        import zstandard as zstd

        cctx = zstd.ZstdCompressor(level=10)
        tar_buf = io.BytesIO()
        with tarfile.open(fileobj=tar_buf, mode="w") as tar:
            for item in sorted(source_dir.glob("**/*")):
                if item.is_file():
                    arcname = item.relative_to(source_dir)
                    tar.add(item, arcname=str(arcname))
        compressed = cctx.compress(tar_buf.getvalue())
        output_archive_path.write_bytes(compressed)
    except ImportError:
        # zstandard未導入時は標準ライブラリの.tar.gzで作成
        gz_path = output_archive_path.with_suffix(".gz")
        with tarfile.open(gz_path, "w:gz") as tar:
            for item in sorted(source_dir.glob("**/*")):
                if item.is_file():
                    arcname = item.relative_to(source_dir)
                    tar.add(item, arcname=str(arcname))
        return gz_path
    return output_archive_path


def generate_dataset_card(law_count: int, article_count: int) -> str:
    """Hugging Face用のREADME.md (Dataset Card)を生成する."""
    return f"""---
license: pddl
language:
- ja
tags:
- legal
- law
- rag
- agentic-rag
- open-knowledge-format
- japan
size_categories:
- 10K<n<100K
---

# 日本法令 Markdown データセット (Japan Laws Markdown for Agentic RAG)

本データセットは、日本の現行法令を **LLM / AIエージェントによる高精度なリーガルリサーチ・RAG** に
最適化された Open Knowledge Format (OKF v0.2) 準拠の Markdown 形式に変換したものです。

変換エンジン: [chottokun/law2markdown](https://github.com/chottokun/law2markdown)

## 特徴
1. **完全な ASIS 原則（無加工・可逆性）**: 条文本文は1文字も改変・要約せず原文保持。
2. **包含階層パス（Hierarchy Path）**: 編・章・節・款・目をスコープ通りに追跡。
3. **双方向参照グラフ**: 他条文への参照（outbound）および被参照（inbound）を索引化。
4. **多階層構文アンカー & オフセット**: 項（`<a id="p1"></a>`）や号の精密Chunkingに対応。
5. **法定用語定義レジストリ**: 法令ごとの定義規定を抽出・相互リンク。

## データセット内容
- **収録法令数**: {law_count} 件
- **総条文レコード数**: {article_count} 条

## 使い方 (How to Use)

### 1. Python `datasets` ライブラリでロード
```python
from datasets import load_dataset

dataset = load_dataset("Chottokun/japan-laws-md", split="train")
print(dataset[0]["title"])
print(dataset[0]["content"])
```

### 2. ローカルナレッジベースとして利用
リポジトリ内の `laws-markdown.tar.zst`（または `.tar.gz`）を展開することで、
条文単位のMarkdownWikiとして即座にローカルRAGやObsidian等に投入できます。

```bash
tar -xf laws-markdown.tar.zst -C ./legal_kb
```

## ライセンス
日本の法令本文は著作権法第13条により著作権の目的となりません（パブリックドメイン / PDDL）。
"""


def upload_to_huggingface(
    repo_id: str,
    token: str,
    files: dict[str, Path],
    dataset_card_content: str,
) -> None:
    """Hugging Face Hub API (REST) を用いてデータセットファイルをアップロードする."""
    # 1. リポジトリの存在確認 / 作成
    create_req = urllib.request.Request("https://huggingface.co/api/repos/create", method="POST")
    create_req.add_header("Authorization", f"Bearer {token}")
    create_req.add_header("Content-Type", "application/json")
    repo_name = repo_id.split("/")[-1]
    body = json.dumps({"name": repo_name, "type": "dataset", "private": False}).encode()
    try:
        with urllib.request.urlopen(create_req, data=body, timeout=15) as res:
            logger.info("Created dataset repo: %s", res.status)
    except urllib.error.HTTPError as e:
        if e.code == 409:
            logger.info("Dataset repo %s already exists.", repo_id)
        else:
            raise RuntimeError(f"Failed to create repo {repo_id}: {e.code} {e.reason}") from e

    # 2. huggingface_hub があれば利用、なければ REST / upload
    try:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        for path_in_repo, local_path in files.items():
            logger.info("Uploading %s to %s...", local_path, path_in_repo)
            api.upload_file(
                path_or_fileobj=str(local_path),
                path_in_repo=path_in_repo,
                repo_id=repo_id,
                repo_type="dataset",
            )
        # README.md
        api.upload_file(
            path_or_fileobj=dataset_card_content.encode("utf-8"),
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
        )
    except Exception as e:
        logger.error("huggingface_hub upload failed: %s", e)
        raise
