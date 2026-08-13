# CHANGELOG

## [0.1.0] - 2026-08-13

### Added (追加)
- e-Gov 法令標準 XML スキーマ v3 準拠 XML の決定論的 Markdown 変換エンジン (`law2markdown`)
- 単一 XML 変換 (`law2md convert`) および ZIP 一括変換 (`law2md convert-zip`) CLI コマンド
- OKF (Open Knowledge Format) v0.1 完全準拠の YAML Frontmatter 修正 (`law_article`, `law_suppl`, `law_appendix`, `law_index`)
- 1条文 1ファイルの可読化出力 (`articles/art_001_第一条.md`)
- 目次 (`index.md`) への条文件名（例: `第一条（目的）`）自動表示機能
- 附則のスマート集約 (`suppl_main.md` / `suppl_amendments.md`)
- 別表の分離維持 (`table_001_別表第一.md`) と様式・付録の集約機能 (`appdx_styles.md`)
- GFM パイプテーブルおよび HTML `<table>` の自動判定レンダリング
- LaTeX (`$ ... $`) 数式自動表記変換
