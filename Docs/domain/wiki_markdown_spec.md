---
type: Concept
title: Wiki用 Markdown 出力詳細仕様書
description: e-Gov 法令データを Wiki / RAG ビューワーに最適化された OKF 準拠 Markdown 群へ変換するための詳細構造・表記・サニタイズ規約
status: active
timestamp: 2026-08-13T00:00:00Z
tags:
  - domain
  - wiki
  - markdown
  - spec
sources:
  - id: plan_md
    resource: /plan/plan.md
    title: e-Gov法令XMLのOpen Knowledge Format（OKF）準拠Markdown変換計画
---

# Wiki用 Markdown 出力詳細仕様書

本ドキュメントは、本プロジェクトにおいて Wiki ビューワー（SimpleWiki, Obsidian, GitHub Pages 等）および LLM / RAG 基盤で運用するための Markdown ファイル群を出力・拡張・新規作成する際の大綱仕様を定義する。

---

## 1. ディレクトリ構造および階層インデックス規定

全階層において 404 エラー（デッドリンク）を発生させず、直感的な閲覧・巡回を保証する「完全ツリー構造」を維持する。

```
<output_root>/
├── index.md                      # [最上位ルートポータル] 収録全法令の種別分類一覧
└── <法令タイトル>/               # [法令フォルダ] (重複時のみ <法令タイトル>_2)
    ├── index.md                  # [法令トップ目次] 条文・附則・付録への総合案内
    ├── articles/                 # 条文フォルダ
    │   ├── index.md              # [サブインデックス] 条文件名付き一覧
    │   ├── art_001_第一条.md
    │   └── art_436-448_...md     # 禁止文字除去済ファイル
    ├── suppl/                    # 附則フォルダ
    │   ├── index.md              # [サブインデックス] 附則区分一覧
    │   ├── suppl_main.md         # 制定時附則
    │   └── suppl_amendments.md   # 沿革・改正附則一覧集約
    └── appendix/                 # 付録フォルダ
        ├── index.md              # [サブインデックス] 別表・様式一覧
        ├── table_001_別表第一.md # 独立別表ファイル
        └── appdx_styles.md       # 様式・図・注の集約ファイル
```

---

## 2. 命名規約およびサニタイズルール

### 2.1 ディレクトリ命名規約
- **原則**: 法令タイトルから記号を除去した「純粋タイトル（最大20文字）」を使用。
- **重複衝突時 (Fail-Safe)**: 同一タイトル（施行日違い等）の重複が発生した場合は、`_2`, `_3` の最小数字サフィックスを付与する。
  - 例: `クレーン等安全規則`, `クレーン等安全規則_2`

### 2.2 ファイル命名および禁止文字サニタイズ
OS 非互換および Web ビューワーでのトラップを防ぐため、すべてのファイル名から **禁止文字 (`:\/*?"<>|`)** を排出し、以下の命名規約を厳守する。

- **禁止文字置換**: コロン `:` やスラッシュ `/` などの記号は安全なハイフン `-` に置換する。
  - 例: `Num="436:448"` → `art_436-448_第四百三十六条から第四百四十八条まで.md`
- **条文ファイル名**: `art_{Num3桁}_{条文タイトル名}.md`（例: `art_001_第一条.md`）
- **別表ファイル名**: `table_{Num3桁}_{別表名}.md`（例: `table_001_別表第一.md`）
- **様式集約ファイル**: `appdx_styles.md`

---

## 3. OKF (Open Knowledge Format) YAML Frontmatter 仕様

すべての出力ファイルは、先頭に `---` で囲まれた YAML Frontmatter を必須で保持する。

### 3.1 `type` フィールド区分一覧

| 種別 (`type`) | 用途 | 配置場所 |
|---|---|---|
| `root_index` | 出力全体の最上位ポータル目次 | `/index.md` |
| `law_index` | 個別法令のトップ総合目次 | `/<LawTitle>/index.md` |
| `law_sub_index` | 子フォルダ用インデックス | `/<LawTitle>/<sub_dir>/index.md` |
| `law_article` | 個別条文 | `/<LawTitle>/articles/art_xxx.md` |
| `law_suppl` | 附則（制定時・沿革） | `/<LawTitle>/suppl/suppl_xxx.md` |
| `law_appendix` | 別表・様式 | `/<LawTitle>/appendix/appdx_xxx.md` |

### 3.2 YAML Frontmatter 記述例 (`law_article`)

```yaml
---
type: law_article
title: "労働基準法 第一条"
law_num: "昭和二十二年法律第四十九号"
law_id: "322AC0000000049_20260717_508AC0000000060"
article_num: "1"
chapter: "第一章　総則"
section: ""
title_kana: "ろうどうきじゅんほう"
promulgate_date: "昭和二十二年四月七日"
enforce_date: "令和八年七月十七日"
sources:
  - law_id: "322AC0000000049_20260717_508AC0000000060"
    law_num: "昭和二十二年法律第四十九号"
timestamp: "2026-08-13T00:00:00Z"
tags:
  - law
  - Act
---
```

---

## 4. 本文 (Body) 描画ルール（完全 ASIS 原本維持）

1. **文字非破壊原則**:
   - ルビ `<Ruby>` の本文文字のみ抽出し、読み `Rt` は除去。法制本文の助詞・語句を1文字も改変・要約しない。
2. **階層文脈 (Breadcrumb Header)**:
   - ファイル本文の先頭（見出し直下）に上位インデックスへのナビゲーションリンクを付与する。
   - 例: `**階層文脈**: [労働基準法](../index.md) > 第一章　総則`
3. **表構造 (Table Rendering)**:
   - 結合セル（`rowspan`/`colspan`）なし → GFM パイプテーブル (`| ... |`)
   - 結合セルあり → HTML `<table>` / `<tr>` / `<td>` タグの構造を維持
4. **数式 (Formula Rendering)**:
   - 算式記号・テキストは LaTeX 表記 (`$ ... $` または `$$ ... $$`) へ変換
5. **ハイパーリンクのポータビリティ**:
   - リンク表記は標準 GFM 相対パス形式 `[表示名](./relative_path.md)` を厳守。
