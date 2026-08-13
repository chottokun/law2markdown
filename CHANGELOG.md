# CHANGELOG

## [0.1.0] - 2026-08-13

### Added (追加)
- ディレクトリ名の極短化・スマート化（OKF Frontmatter に `law_id` を保持しているため、原則「法令タイトルのみ」にシンプル化。同一タイトルのバージョン重複時のみ自動フォールバックで ID 付与）
- 出力先ディレクトリ直下への**最上位ルート目次 (`output_sample/index.md`) 自動生成機能**（全法令を「法律」「政令」「省令」等の種別ごとに自動グルーピング・未施行タグ表示付きでポータル表示）
- CSV メタデータ自動補完機能 (`20.csv` 等の同封 CSV から `title_kana`, `promulgate_date`, `enforce_date`, `amend_law_title`, `amend_law_num`, `is_unexecuted` を自動抽出・Frontmatter付与)
- e-Gov 法令標準 XML スキーマ v3 準拠 XML の決定論的 Markdown 変換エンジン (`law2markdown`)
- 単一 XML 変換 (`law2md convert`) および ZIP 一括変換 (`law2md convert-zip`) CLI コマンド
- OKF (Open Knowledge Format) v0.1 完全準拠の YAML Frontmatter 修正 (`law_article`, `law_suppl`, `law_appendix`, `law_index`)
- 1条文 1ファイルの可読化出力 (`articles/art_001_第一条.md`)
- 目次 (`index.md`) への条文件名（例: `第一条（目的）`）自動表示機能
- 附則のスマート集約 (`suppl_main.md` / `suppl_amendments.md`)
- 別表の分離維持 (`table_001_別表第一.md`) と様式・付録の集約機能 (`appdx_styles.md`)
- GFM パイプテーブルおよび HTML `<table>` の自動判定レンダリング
- LaTeX (`$ ... $`) 数式自動表記変換
