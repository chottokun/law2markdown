# LLM-Wiki 変更ログ

## 2026-08-13
- Wiki用 Markdown 出力詳細仕様書 (`Docs/domain/wiki_markdown_spec.md`) の作成・ナレッジベース登録。階層ツリー構造、OKF Frontmatter型規約、禁止文字サニタイズ、ASIS本文ルールを明文化。
- 全ドキュメント類（`README.md`, `Docs/domain/law_converter.md`, `CHANGELOG.md` 等）の最新仕様への完全同期・更新完了。
- ファイル名・パス生成における OS 禁止文字（`:` `\` `*` `?` `"` `<` `>` `|`）のサニタイズ処理を実装。複数条文指定のコロン `:` を安全なハイフン `-` に自動置換（`art_436-448...md`）。不正ファイル数 93 件 → 0 件を達成。
- 重複が発生した際のディレクトリ命名を長い法令ID付与から【案1】シンプル連番 (`_2`, `_3` ...) に変更し、フォルダ名の無駄な長大化を完全排除。
- ディレクトリ命名ロジックを【案B】タイトル優先にリファクタリング。OKF Frontmatter に `law_id` を保持しているためフォルダ名を `output_sample/じん肺法/` のように極短・スマート化。
- 出力先ディレクトリ直下への最上位ルート目次 (`output_sample/index.md`) 自動生成機能の実装。全収録法令を種別（法律・政令・省令等）にグルーピングし、Webビューワー（SimpleWiki等）でのトップポータル画面を提供。
- CSV メタデータ自動補完機能 (`csv_parser.py`) の実装完了。`20.csv` 等から `title_kana`, `promulgate_date`, `enforce_date`, `amend_law_title`, `amend_law_num`, `is_unexecuted` を抽出して YAML Frontmatter に自動付与。
- e-Gov 法令 XML から OKF 準拠 Markdown 変換エンジン (`law2markdown`) Phase 1 MVP の構築完了。
- 法令標準 XML スキーマ v3 への適合（憲法、法律、政令、省令、勅令、規則等の全種別）。
- OKF v0.1 YAML Frontmatter 完全準拠 (`law_article`, `law_suppl`, `law_appendix`, `law_index`)。
- 条文件名付き目次 (`index.md`)、附則の2ファイルスマート集約、様式・付録集約機能の実装。