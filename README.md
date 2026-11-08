# law2markdown

[![Hugging Face Datasets](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Datasets-yellow)](https://huggingface.co/datasets/Chottokun/japan-laws-md)
[![GitHub Releases](https://img.shields.io/github/v/release/chottokun/law2markdown?label=Releases)](https://github.com/chottokun/law2markdown/releases)
[![License: PDDL](https://img.shields.io/badge/License-PDDL-blue.svg)](https://opendatacommons.org/licenses/pddl/)
[![CI](https://github.com/chottokun/law2markdown/actions/workflows/ci.yml/badge.svg)](https://github.com/chottokun/law2markdown/actions/workflows/ci.yml)

e-Gov 法令 XML データを、LLM / RAG および Web ビューワー（SimpleWiki 等）に最適化された **Open Knowledge Format (OKF)** 準拠の Markdown ファイル群へ**決定論的にパース・変換する CLI ツール**。

---

## 📦 公開データセットを今すぐ利用する

本ツールで変換された日本法令データセット（全公開法令および主要法令）は、**Hugging Face Datasets** および **GitHub Releases** にて完全無料・パブリックドメイン（著作権法第13条準拠）で公開・毎週定期更新されています。

### 1. Python (`datasets`) で条文を 1 行読み込み
```python
from datasets import load_dataset

# Hugging Face から直接ロード（Parquet形式で超高速・ストリーミング可能）
dataset = load_dataset("Chottokun/japan-laws-md", split="train")

# 条文の参照・階層パス・本文・定義語にアクセス
article = dataset[0]
print(article["title"])  # 例: 日本国憲法 第一条
print(article["hierarchy_path"])  # 例: 日本国憲法 > 第一章　天皇 > 第一条
print(article["content"])  # 原本そのままの条文Markdown
```

### 2. ローカルナレッジベース（Markdown Wiki）として一括ダウンロード
* [GitHub Releases](https://github.com/chottokun/law2markdown/releases) または [Hugging Face Files](https://huggingface.co/datasets/Chottokun/japan-laws-md/tree/main) から `laws-markdown.tar.gz` をダウンロードして解凍するだけで、条文単位（1条文1ファイル＋相互リンク完備）のローカルWikiが即座に構築できます。

---

## 🌟 主な特徴

- **全法令種別対応 (法令標準 XML スキーマ v3 適合)**
  - 憲法、法律、政令、勅令、府省令、規則、告示等の全ての e-Gov 法令 XML をパース。
- **完全 ASIS（原本維持）原則**
  - 法令本文の文字・助詞を 1 文字も改変せず、原文通りのテキストを維持。
  - ルビ（`<Ruby>/<Rt>`）は親文字のみ非破壊抽出。
  - 複雑な結合表は HTML `<table>`、数式は LaTeX (`$ ... $`) で GitHub Markdown 準拠レンダリング。
- **OKF v0.2 完全準拠 & メタデータ自動補完**
  - 全てのファイル（条文・附則・付録・目次）に `type`, `title`, `description`, `resource`（公式 e-Gov パーマリンク `https://laws.e-gov.go.jp/document?lawid=...`）, `status`, `generated: {by, at}`, `sources: [{id, resource, title, ...}]`, `tags` を含む [OKF v0.2](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/refs/heads/main/okf/SPEC.md) 仕様の YAML Frontmatter を完全付与。
  - 同封 CSV (`20.csv` 等) から `title_kana`, `promulgate_date`, `enforce_date`, `amend_law_title`, `amend_law_num`, `is_unexecuted` を自動抽出して Frontmatter に統合。
- **Agentic Legal RAG（自律的法探索基盤）高度化機能**
  - **完全階層パス (`hierarchy_path`)**: パンデクテン体系（編・章・節・款・目・条）をスコープ制御付きで追跡し、条文単体でベクトル化された場合も規律文脈を完全維持。
  - **相互参照・委任グラフ (`outbound` / `inbound`)**: 条文内の相対参照（前条・次条）・明示参照（第〇条）・別表・政令委任を決定論的に抽出し、双方向グラフを Frontmatter および末尾セクションに自動構築。
  - **法定用語定義レジストリ (`definitions.md`)**: 「〜とは、〜をいう」「以下〜という」等の定義規定から専門用語を自動索引化し、俗用意味と法的限定意味の混同を防止。
  - **項・号行頭アンカー (`child_anchors`)**: 本文の文言を一切改変せず（原本維持）、項・号・細分号の行頭に `<a id="..."></a>` を配置し、Parent Document Retrieval における微小ブロックの検索・オフセット範囲を提供。
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

`uv run law2md` コマンドを使用して変換および探索を行います。

### 1. 単一 XML ファイルの変換

```bash
uv run law2md convert path/to/law.xml -o ./output
```

### 2. e-Gov 分類 ZIP ファイルの一括変換

```bash
uv run law2md convert-zip data/20_xml.zip -o ./output
```

### 3. 法探索クエリ (`query`)

```bash
# 条文または特定項の本文・メタデータ取得
uv run law2md query get-article 労働基準法 1 -p 2 -d ./output

# 上位階層および関連条文一覧の取得
uv run law2md query get-hierarchy 労働基準法 1 -d ./output

# 相互参照グラフ（参照先・被参照元）の走査
uv run law2md query trace-references 労働基準法 1 -d ./output

# 法定用語の厳密な定義照会
uv run law2md query lookup-term 労働基準法 労働者 -d ./output
```

### 4. Agentic RAG 用 MCP サーバー起動 (`mcp`)

Claude Desktop や自律的 AI エージェントから上記の法探索ツールを呼び出すための stdio サーバーを起動します。

```bash
uv run law2md mcp -d ./output
```

### 5. データセット構築・Hugging Face 公開 (`dataset`)

主要法令（憲法、民法、刑法、商法等）の自動取得、条文Parquet作成、Markdownアーカイブ生成、Hugging Faceへの公開を一括実行します。

```bash
# Hugging Face Datasets へ自動公開
HF_TOKEN="<your_token>" uv run law2md dataset build --scope core --upload-hf --repo-id "Chottokun/japan-laws-md"
```

> [!TIP]
> 公開済みデータセットは Hugging Face Datasets [Chottokun/japan-laws-md](https://huggingface.co/datasets/Chottokun/japan-laws-md) から誰でも Python 1行（`load_dataset("Chottokun/japan-laws-md")`）またはアーカイブ解凍で即座に利用可能です。

---

## 📁 出力構造

```
output/
├── index.md                      # [最上位ポータル目次] 全法令の自動分類一覧
├── 労働基準法/                   # [極短フォルダ名] (重複時のみ 労働基準法_2)
│   ├── index.md                  # [法令トップ目次] 条文・附則・付録・用語定義への総合案内
│   ├── definitions.md            # [用語定義レジストリ] 法令内の定義用語・定義条文一覧
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

## 📚 ドキュメント (LLM-Wiki / OKF)

プロジェクトの設計方針、変換仕様、アーキテクチャの詳細は [`docs/`](./docs/README.md) 配下に OKF (Open Knowledge Format v0.2) 形式で整備されています。

* [📑 ナレッジインデックス (`docs/README.md`)](./docs/README.md)
  * [🏛️ Architecture (`docs/architecture/`)](./docs/architecture/README.md): 全体パイプライン設計・決定論的変換設計
  * [📖 Domain (`docs/domain/`)](./docs/domain/README.md): 法令 XML 変換仕様・Wiki用 Markdown / Frontmatter 詳細仕様
  * [⚙️ Infrastructure (`docs/infrastructure/`)](./docs/infrastructure/README.md): Python/uv 実行環境および CLI 仕様
  * [📝 Change Log (`docs/log.md`)](./docs/log.md): ナレッジベースの更新履歴

---

## 📜 ライセンス

[MIT License](LICENSE)
