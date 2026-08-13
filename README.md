# law2markdown

e-Gov 法令 XML データを、LLM / RAG および Web ビューワー（SimpleWiki 等）に最適化された **Open Knowledge Format (OKF)** 準拠の Markdown ファイル群へ**決定論的にパース・変換する CLI ツール**。

---

## 🌟 主な特徴

- **全法令種別対応 (法令標準 XML スキーマ v3 適合)**
  - 憲法、法律、政令、勅令、府省令、規則、告示等の全ての e-Gov 法令 XML をパース。
- **完全 ASIS（原本維持）原則**
  - 法令本文の文字・助詞を 1 文字も改変せず、原文通りのテキストを維持。
  - ルビ（`<Ruby>/<Rt>`）は親文字のみ非破壊抽出。
  - 複雑な結合表は HTML `<table>`、数式は LaTeX (`$ ... $`) で GitHub Markdown 準拠レンダリング。
- **OKF v0.1 完全準拠**
  - 全てのファイルに `type`, `title`, `sources` 等を含む YAML Frontmatter を付与。
- **高閲覧性・スマート構造化**
  - **1条文 = 1ファイル** (`articles/art_001_第一条.md`)
  - **目次 (`index.md`)**: 各条文の件名（`第一条（目的）`）を表示し、全体を直感的に俯瞰可能。
  - **附則のスマート集約**: 制定時附則 (`suppl_main.md`) と 沿革・改正附則一覧 (`suppl_amendments.md`) に集約。
  - **様式・付録の自動集約**: 別表は個別に分離維持、様式・付録は `appdx_styles.md` に集約。

---

## 🚀 セットアップ

### 前提条件
- Python 3.12+
- `uv` (推奨パッケージマネージャ)

### インストール

```bash
# クローン
git clone https://github.com/user/law2markdown.git
cd law2markdown

# 依存関係の同期
uv sync
```

---

## 💻 使い方 (CLI)

`uv run law2md` コマンドを使用して変換を行います。

### 1. 単一 XML ファイルの変換

```bash
uv run law2md convert path/to/law.xml -o ./output
```

### 2. e-Gov 分類 ZIP ファイルの一括変換

```bash
uv run law2md convert-zip data/20_xml.zip -o ./output
```

---

## 📁 出力構造

```
output/
└── 労働基準法_322AC0000000049_20260717_508AC0000000060/
    ├── index.md                  # 法令トップ・件名付き目次
    ├── articles/                 # 条文フォルダ (1条文 = 1ファイル)
    │   ├── art_001_第一条.md
    │   ├── art_002_第二条.md
    │   └── art_2_2_第二条の二.md
    ├── suppl/                    # 附則フォルダ
    │   ├── suppl_main.md         # 制定時附則
    │   └── suppl_amendments.md   # 沿革・改正附則一覧
    └── appendix/                 # 付録フォルダ
        ├── table_001_別表第一.md # 独立別表
        └── appdx_styles.md       # 様式・図・付録一覧集約ファイル
```

---

## 🧪 開発・テスト

```bash
# テスト実行
uv run pytest

# Lint / Format チェック
uv run ruff check
uv run ruff format --check

# セキュリティ監査
uv audit
```

---

## 📜 ライセンス

[MIT License](LICENSE)
