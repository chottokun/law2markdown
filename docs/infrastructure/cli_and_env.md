---
type: Configuration
title: 実行環境と CLI 仕様
description: Python 3.12+ / uv 環境構成および law2md CLI コマンドの使用方法・オプション仕様
status: stable
generated:
  by: agent/gemini-3.7-flash
  at: 2026-08-14T20:45:00+09:00
tags:
  - infrastructure
  - cli
  - python
  - uv
sources:
  - id: plan_md
    resource: /plan/plan.md
    title: e-Gov法令XMLのOpen Knowledge Format（OKF）準拠Markdown変換計画
---

# 実行環境と CLI 仕様

## 1. 概要

本プロジェクトは Python 3.12+ および `uv` パッケージマネージャーを標準の開発・実行基盤として採用しています。

## 2. 実行環境要件

- **Python**: 3.12+
- **パッケージマネージャー**: `uv`
- **主要依存ライブラリ**:
  - `click` (CLI インターフェース)
  - `pyyaml` (YAML Frontmatter 生成・検証)
  - `pytest`, `pytest-cov`, `ruff`, `mypy` (テスト・静的解析)

## 3. CLI コマンド仕様

`law2md` コマンドは `pyproject.toml` の `[project.scripts]` で定義されています。

### 3.1 単一 XML 変換 (`convert`)

```bash
uv run law2md convert <path/to/law.xml> -o <output_dir>
```

- **引数**: XML ファイルパス
- **オプション**:
  - `-o, --output-dir`: 出力先ルートディレクトリ（必須）
  - `--law-id`: 法令 ID の明示的指定（任意）

### 3.2 法令 ZIP 変換 (`convert-zip`)

```bash
uv run law2md convert-zip <path/to/law.zip> -o <output_dir>
```

- **引数**: e-Gov 法令 ZIP アーカイブパス（XML および メタデータ CSV を内包）
- **オプション**:
  - `-o, --output-dir`: 出力先ルートディレクトリ（必須）

### 3.3 法探索クエリ (`query`)

変換済みナレッジベースから、特定条文・項スライス・上位階層・相互参照・定義語を直接照会します。

```bash
# 1. 条文または特定項の取得
uv run law2md query get-article <法令名> <条番号> [-p <項番号>] [-d <kb_dir>]

# 2. 上位階層および関連条文一覧の取得
uv run law2md query get-hierarchy <法令名> <条番号> [-d <kb_dir>]

# 3. 参照関係（参照先・被参照元）のグラフ走査
uv run law2md query trace-references <法令名> <条番号> [--direction {outbound,inbound,both}] [-d <kb_dir>]

# 4. 法定用語の厳密な定義照会
uv run law2md query lookup-term <法令名> <専門用語> [-d <kb_dir>]
```

### 3.4 MCP サーバー起動 (`mcp`)

Model Context Protocol (MCP) stdio JSON-RPC 2.0 サーバーを起動し、Claude Desktop や AI エージェントから4つの探索ツールを利用可能にします。

```bash
uv run law2md mcp -d <output_dir>
```

### 3.5 データセット構築・配信 (`dataset`)

日本の主要法令または一括法令を取得し、Parquetテーブル（Hugging Face向け）およびMarkdownアーカイブ（GitHub Releases向け）を構築・自動公開します。

```bash
# 主要法令（憲法、民法、刑法、商法等）の取得・変換・Parquet/アーカイブ構築・Hugging Face公開
uv run law2md dataset build --scope core --upload-hf --repo-id "Chottokun/japan-laws-md"
```

- **オプション**:
  - `--scope {core,custom}`: 法令取得スコープ（デフォルト: `core`）
  - `-o, --output-dir`: ナレッジベース出力ディレクトリ
  - `--parquet-out`: Parquetファイル出力先
  - `--archive-out`: Markdownアーカイブ出力先（`.tar.zst` または `.tar.gz`）
  - `--upload-hf`: Hugging Face Datasets への自動アップロード
  - `--repo-id`: Hugging Face データセットID（例: `Chottokun/japan-laws-md`）
  - `--token`: HF アクセストークン（未指定時は `HF_TOKEN` 環境変数）

## 4. CI/CD ワークフロー (GitHub Actions)

* `.github/workflows/ci.yml`: PR および `main` ブランチへのプッシュ時に自動でテスト・リント・フォーマット検証を実行。
* `.github/workflows/build-dataset.yml`: 毎週日曜日（日本時間 月曜未明）の定期実行または手動トリガー（`workflow_dispatch`）により、法令データセットの自動ビルド・Hugging Face 公開・GitHub Releases 添付を実行。

## 5. 関連概念

* [変換パイプライン アーキテクチャ](../architecture/pipeline.md) - 内部コンポーネント詳細
* [Wiki用 Markdown 出力詳細仕様書](../domain/wiki_markdown_spec.md) - 出力される Markdown の詳細構造

