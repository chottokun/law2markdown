"""Unit tests for law2markdown dataset module."""

import tempfile
from pathlib import Path

import pyarrow.parquet as pq

from law2markdown.dataset import (
    collect_article_records,
    create_markdown_tar_zst,
    export_articles_parquet,
    generate_dataset_card,
    parse_frontmatter,
)


def test_parse_frontmatter() -> None:
    text = """---
title: "テスト法律 第一条"
law_id: "123TEST"
outbound_references:
  - "art_002_第二条"
  - "art_003_第三条"
inbound_references: []
---

# 第一条
本文テキストです。
"""
    meta, body = parse_frontmatter(text)
    assert meta["title"] == "テスト法律 第一条"
    assert meta["law_id"] == "123TEST"
    assert meta["outbound_references"] == ["art_002_第二条", "art_003_第三条"]
    assert meta["inbound_references"] == []
    assert "# 第一条\n本文テキストです。" in body


def test_collect_and_export_parquet() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir) / "test_law"
        art_dir = kb_dir / "articles"
        art_dir.mkdir(parents=True)

        sample_article = art_dir / "art_001_第一条.md"
        sample_article.write_text(
            """---
title: "テスト法 第一条"
law_id: "999TEST"
law_num: "令和四年法律第一号"
article_num: "1"
hierarchy_path: "テスト法 > 第一条"
outbound_references: []
inbound_references: []
defined_terms: ["テスト用語"]
child_anchors:
  - id: "p1"
    level: "paragraph"
    label: "第1項"
    start_offset: 10
    end_offset: 50
---

<a id="p1"></a>テスト本文
""",
            encoding="utf-8",
        )

        records = collect_article_records(Path(tmpdir))
        assert len(records) == 1
        rec = records[0]
        assert rec.law_id == "999TEST"
        assert rec.title == "テスト法 第一条"
        assert rec.defined_terms == ["テスト用語"]
        assert "p1" in rec.child_anchors_json

        parquet_out = Path(tmpdir) / "output.parquet"
        export_articles_parquet(records, parquet_out)
        assert parquet_out.exists()

        table = pq.read_table(parquet_out)
        assert table.num_rows == 1
        assert "hierarchy_path" in table.column_names
        assert table["law_id"][0].as_py() == "999TEST"


def test_create_markdown_archive() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "kb"
        src.mkdir()
        (src / "test.md").write_text("hello law", encoding="utf-8")

        archive_out = Path(tmpdir) / "kb.tar.zst"
        res_path = create_markdown_tar_zst(src, archive_out)
        assert res_path.exists()
        assert res_path.stat().st_size > 0


def test_generate_dataset_card() -> None:
    card = generate_dataset_card(14, 500)
    assert "Chottokun/japan-laws-md" in card
    assert "**収録法令数**: 14 件" in card
    assert "**総条文レコード数**: 500 条" in card
