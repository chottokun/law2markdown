# law2markdown

[![Hugging Face Datasets](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Datasets-yellow)](https://huggingface.co/datasets/Chottokun/japan-laws-md)
[![GitHub Releases](https://img.shields.io/github/v/release/chottokun/law2markdown?label=Releases)](https://github.com/chottokun/law2markdown/releases)
[![License: PDDL](https://img.shields.io/badge/License-PDDL-blue.svg)](https://opendatacommons.org/licenses/pddl/)
[![CI](https://github.com/chottokun/law2markdown/actions/workflows/ci.yml/badge.svg)](https://github.com/chottokun/law2markdown/actions/workflows/ci.yml)

e-Gov 法令 XML データを、Open Knowledge Format (OKF) 準拠の Markdown ファイル群へ決定論的に変換する CLI ツールです。条文単位のファイル分割、包含階層のメタデータ付与、相互参照関係の抽出、および RAG（Retrieval-Augmented Generation）向けインデックスの生成を行います。

---

## 公開データセット

本ツールで変換した日本法令データセット（全法令および主要基本法令）は、Hugging Face Datasets および GitHub Releases にて公開・定期更新されています（日本の法令本文は著作権法第13条第1号により著作権の目的となりません）。

### Python (`datasets`) による読み込み
```python
from datasets import load_dataset

# Hugging Face から直接ロード（Parquet 形式、ストリーミング取得可能）
dataset = load_dataset("Chottokun/japan-laws-md", split="train")

article = dataset[0]
print(article["title"])  # 例: 日本国憲法 第一条
print(article["hierarchy_path"])  # 例: 日本国憲法 > 第一章　天皇 > 第一条
print(article["content"])  # 条文本文（Markdown）
```

### アーカイブ（Markdown 一式）の利用
[GitHub Releases](https://github.com/chottokun/law2markdown/releases) または [Hugging Face Files](https://huggingface.co/datasets/Chottokun/japan-laws-md/tree/main) から `laws-markdown.tar.gz` をダウンロードして解凍することで、条文単位で相互リンクされたローカルナレッジベースとして利用できます。

---

## 仕様と機能

- **法令 XML スキーマ対応**
  - 法令標準 XML スキーマ v3 に適合（憲法、法律、政令、勅令、府省令、規則、告示）。
- **条文テキストの原本保持（ASIS）**
  - 条文本文の要約や改変を行わず、原文テキストを維持。
  - ルビ（`<Ruby>/<Rt>`）は親文字を抽出。
  - 表（`TableStruct`）は HTML `<table>`、数式（`ArithFormula`）は LaTeX (`$ ... $`) で出力。
- **OKF v0.2 準拠のメタデータ付与**
  - 条文・附則・付録・目次の各ファイルに YAML Frontmatter（`type`, `title`, `description`, `resource`, `status`, `generated`, `sources`, `tags`）を付与。
  - 同封 CSV から公布日、施行日、改正情報、未施行フラグを抽出して統合。
- **法探索（RAG）向け構造化**
  - **包含階層パス (`hierarchy_path`)**: 編・章・節・款・目をスコープに沿って追跡し、条文 Frontmatter に記載。
  - **相互参照関係 (`outbound_references` / `inbound_references`)**: 相対参照（前条・次条）、明示参照（第〇条）、別表、政令委任を抽出し、双方向の参照関係を Frontmatter および末尾セクションに出力。
  - **用語定義レジストリ (`definitions.md`)**: 「〜とは、〜をいう」「以下〜という」等の定義規定から専門用語と定義元条文を抽出し、一覧化。
  - **構文アンカーとオフセット (`child_anchors`)**: 項および号の行頭に `<a id="..."></a>` を配置し、Frontmatter に文字オフセット範囲（`start_offset`, `end_offset`）を記録。
- **ファイル・ディレクトリ構成**
  - 1 条文 = 1 ファイル（`articles/art_001_第一条.md`）。
  - 同名法令は公布日・施行日等でソートし、枝番（`_2`, `_3`）により決定論的に重複を回避。
  - ファイル名禁止文字（`:` 等）はハイフンに置換。

---

## セットアップ

### 前提条件
- Python 3.12+
- `uv`

### インストール

```bash
git clone https://github.com/chottokun/law2markdown.git
cd law2markdown
uv sync
```

---

## 使用方法

### 1. 単一 XML ファイルの変換

```bash
uv run law2md convert path/to/law.xml -o ./output
```

### 2. e-Gov 分類 ZIP ファイルの一括変換

```bash
uv run law2md convert-zip data/category.zip -o ./output
```

### 3. 法探索クエリ (`query`)

```bash
# 条文または特定項の本文取得
uv run law2md query get-article 労働基準法 1 -p 2 -d ./output

# 上位階層および同一階層の条文一覧取得
uv run law2md query get-hierarchy 労働基準法 1 -d ./output

# 参照関係（参照先・被参照元）の走査
uv run law2md query trace-references 労働基準法 1 -d ./output

# 法定用語の定義照会
uv run law2md query lookup-term 労働基準法 労働者 -d ./output
```

### 4. MCP サーバー起動 (`mcp`)

Claude Desktop 等の MCP クライアント向け stdio サーバーを起動します。

```bash
uv run law2md mcp -d ./output
```

### 5. データセット構築・Hugging Face 公開 (`dataset`)

主要基本法令（`--scope core`）または全法令（`--scope all`）の取得・変換・Parquet 出力・アーカイブ化・Hugging Face へのアップロードを行います。

```bash
# 主要法令の構築と Hugging Face への公開
HF_TOKEN="<your_token>" uv run law2md dataset build --scope core --upload-hf --repo-id "Chottokun/japan-laws-md"

# 全法令の一括構築
uv run law2md dataset build --scope all -o ./output/legal_kb
```

---

## 出力ディレクトリ構造

```
output/
├── index.md                      # 全法令一覧目次
├── 労働基準法/                   # 法令フォルダ
│   ├── index.md                  # 法令目次
│   ├── definitions.md            # 用語定義一覧
│   ├── articles/                 # 条文フォルダ (1条文 = 1ファイル)
│   │   ├── index.md              # 条文一覧
│   │   ├── art_001_第一条.md
│   │   └── art_436-448_...md
│   ├── suppl/                    # 附則フォルダ
│   │   ├── index.md              # 附則一覧
│   │   ├── suppl_main.md         # 制定時附則
│   │   └── suppl_amendments.md   # 改正附則集約
│   └── appendix/                 # 付録フォルダ
│       ├── index.md              # 付録一覧
│       ├── table_001_別表第一.md # 別表
│       └── appdx_styles.md       # 様式・図集約
```

---

## テスト

```bash
# テスト実行
uv run pytest

# 静的解析・フォーマット検証
uv run ruff check
uv run ruff format --check

# セキュリティ監査
uv run audit
```

---

## ドキュメント

プロジェクトの設計方針、変換仕様、アーキテクチャの詳細は [`docs/`](./docs/README.md) 配下に OKF (Open Knowledge Format v0.2) 形式で整備されています。

* [ナレッジインデックス (`docs/README.md`)](./docs/README.md)
  * [Architecture (`docs/architecture/`)](./docs/architecture/README.md): 全体パイプライン設計
  * [Domain (`docs/domain/`)](./docs/domain/README.md): 法令 XML 変換仕様・Markdown 出力仕様
  * [Infrastructure (`docs/infrastructure/`)](./docs/infrastructure/README.md): 実行環境および CLI 仕様
  * [Change Log (`docs/log.md`)](./docs/log.md): 更新履歴

---

## ライセンス

* ツール本体: [MIT License](LICENSE)
* 法令本文データ: パブリックドメイン（著作権法第13条第1号）
