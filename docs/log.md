# LLM-Wiki 変更ログ

## 2026-08-15
* **Creation**: リンク完全性検証エンジン (`validator.py`) の新規実装。出力された全 Markdown ファイル内の相対リンク（`[...](./...)`）を網羅的に走査し、リンク切れ（404）や存在しないファイル参照を自動検出・検証。
* **Creation**: CLI 変換完了時における「📊 変換・整合性監査レポート」自動出力機能の実装。総ファイル数、法令・条文・附則・別表/様式の内訳、検証リンク数、リンク完全性（PASS/FAIL）を即座にサマリー表示。
* **Fix**: ZIP一括変換時に同名法令（施行日違い等）が存在する場合のディレクトリ重複解決をリファクタリング。事後リネームによる先行出力データの上書き・最上位 `index.md` からのリンク切れ（404）を解消するため、書き込み前に施行日・公布日・法令IDで決定論的ソートを行い、衝突しない出力先ディレクトリ（`_2`, `_3` 等）を事前決定して直接書き出すアーキテクチャへ移行。
* **Update**: ドメイン仕様書 (`docs/domain/wiki_markdown_spec.md`) およびアーキテクチャ文書 (`docs/architecture/pipeline.md`) を最新実装に同期更新。

## 2026-08-14
* **Update**: OKF (Open Knowledge Format v0.2) 仕様に完全準拠するよう YAML フロントマター生成部（`frontmatter.py`）を改訂。`type`, `title`, `description`, `resource`（公式 e-Gov パーマリンク `https://laws.e-gov.go.jp/document?lawid=...`）, `status`, `generated: {by: "process:law2markdown", at: ...}`, `sources: [{id, resource, title, ...}]`, `tags` を標準出力。過剰な監査・統計フィールドを排除した最適なスキーマを策定。
* **Update**: ドメイン仕様書 `docs/domain/wiki_markdown_spec.md` に OKF v0.2 フロントマター仕様および e-Gov URL 体系を追記。
* **Update**: OKF (Open Knowledge Format v0.2) 運用プロシージャに基づき `docs/` 配下のナレッジベース構造を完全整備。
* **Creation**: 最上位インデックス `docs/README.md` および各カテゴリインデックス（`docs/architecture/README.md`, `docs/domain/README.md`, `docs/infrastructure/README.md`）の作成。
* **Creation**: アーキテクチャ概念文書 `docs/architecture/pipeline.md`（全体パイプライン設計・Mermaid フロー図）の追加。
* **Creation**: インフラ概念文書 `docs/infrastructure/cli_and_env.md`（Python 3.12/uv 実行環境および CLI コマンド仕様）の追加。
* **Update**: ドメイン概念文書（`docs/domain/law_converter.md`, `docs/domain/wiki_markdown_spec.md`）の YAML フロントマターを OKF v0.2 標準（`type`, `status: stable`, `generated: {by, at}`, `sources`）に正規化。
* **Update**: 法令 ZIP 内の CSV ファイル（`1.csv`, `2.csv` 等の連番・複数 CSV）自動探索およびメタデータ統合仕様の検証・ドキュメント（`docs/domain/law_converter.md`）同期完了。

## 2026-08-13
* **Creation**: Wiki用 Markdown 出力詳細仕様書 (`docs/domain/wiki_markdown_spec.md`) の作成・ナレッジベース登録。階層ツリー構造、OKF Frontmatter型規約、禁止文字サニタイズ、ASIS本文ルールを明文化。
* **Update**: 全ドキュメント類（`README.md`, `docs/domain/law_converter.md`, `CHANGELOG.md` 等）の最新仕様への完全同期・更新完了。
* **Update**: ファイル名・パス生成における OS 禁止文字（`:` `\` `*` `?` `"` `<` `>` `|`）のサニタイズ処理を実装。複数条文指定のコロン `:` を安全なハイフン `-` に自動置換（`art_436-448...md`）。不正ファイル数 93 件 → 0 件を達成。
* **Update**: 重複が発生した際のディレクトリ命名を長い法令ID付与から【案1】シンプル連番 (`_2`, `_3` ...) に変更し、フォルダ名の無駄な長大化を完全排除。
* **Update**: ディレクトリ命名ロジックを【案B】タイトル優先にリファクタリング。OKF Frontmatter に `law_id` を保持しているためフォルダ名を `output_sample/じん肺法/` のように極短・スマート化。
* **Creation**: 出力先ディレクトリ直下への最上位ルート目次 (`output_sample/index.md`) 自動生成機能の実装。全収録法令を種別（法律・政令・省令等）にグルーピングし、Webビューワー（SimpleWiki等）でのトップポータル画面を提供。
* **Creation**: CSV メタデータ自動補完機能 (`csv_parser.py`) の実装完了。`20.csv` 等から `title_kana`, `promulgate_date`, `enforce_date`, `amend_law_title`, `amend_law_num`, `is_unexecuted` を抽出して YAML Frontmatter に自動付与。
* **Creation**: e-Gov 法令 XML から OKF 準拠 Markdown 変換エンジン (`law2markdown`) Phase 1 MVP の構築完了。
* **Update**: 法令標準 XML スキーマ v3 への適合（憲法、法律、政令、省令、勅令、規則等の全種別）。
* **Update**: OKF v0.1 YAML Frontmatter 完全準拠 (`law_article`, `law_suppl`, `law_appendix`, `law_index`)。
* **Creation**: 条文件名付き目次 (`index.md`)、附則の2ファイルスマート集約、様式・付録集約機能の実装。