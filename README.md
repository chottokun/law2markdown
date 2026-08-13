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
- **OKF v0.1 完全準拠 & メタデータ自動補完**
  - 全てのファイル（条文・附則・付録・目次）に `type`, `title`, `sources` を含む YAML Frontmatter を完全付与。
  - 同封 CSV (`20.csv` 等) から `title_kana`, `promulgate_date`, `enforce_date`, `amend_law_title`, `amend_law_num`, `is_unexecuted` を自動抽出して Frontmatter に統合。
- **高閲覧性・完全インデックス化ツリー**
  - **極短シンプルフォルダ名**: `output/労働基準法/`, 重複時も `_2`, `_3` の最小連番。
  - **最上位ポータル目次 (`output/index.md`)**: 法令種別（法律・政令・省令等）の自動分類・未施行タグ付き表示。
  - **全サブディレクトリインデックス (`index.md`)**: `articles/index.md`, `suppl/index.md`, `appendix/index.md` を完備し、Web ビューワーでの 404 エラーや手詰まりを100%防止。
  - **OS禁止文字サニタイズ**: 複数条文指定等のコロン `:` をハイフン `-`（`art_436-448...md`）へ完全変換し、クロスプラットフォームでの互換性を保証。

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
├── index.md                      # [最上位ポータル目次] 全法令の自動分類一覧
├── 労働基準法/                   # [極短フォルダ名] (重複時のみ 労働基準法_2)
│   ├── index.md                  # [法令トップ目次] 条文・附則・付録への案内
│   ├── articles/                 # 条文フォルダ (1条文 = 1ファイル)
│   │   ├── index.md              # 条文サブインデックス
│   │   ├── art_001_第一条.md
│   │   └── art_436-448_...md     # [サニタイズ済] 禁止文字除去済ファイル名
│   ├── suppl/                    # 附則フォルダ
│   │   ├── index.md              # 附則サブインデックス
│   │   ├── suppl_main.md         # 制定時附則
│   │   └── suppl_amendments.md   # 沿革・改正附則一覧集約
│   └── appendix/                 # 付録フォルダ
│       ├── index.md              # 付録サブインデックス
│       ├── table_001_別表第一.md # 独立別表
│       └── appdx_styles.md       # 様式・図・付録一覧集約
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
