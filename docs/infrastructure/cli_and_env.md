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

## 4. 関連概念

* [変換パイプライン アーキテクチャ](../architecture/pipeline.md) - 内部コンポーネント詳細
* [Wiki用 Markdown 出力詳細仕様書](../domain/wiki_markdown_spec.md) - 出力される Markdown の詳細構造
