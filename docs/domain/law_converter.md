---
type: Concept
title: 法令 XML から OKF Markdown への変換仕様
description: e-Gov 法令標準 XML スキーマ v3 を OKF 準拠の Markdown ナレッジファイル群へ非破壊的変換するアーキテクチャ・ルール
status: active
timestamp: 2026-08-13T00:00:00Z
tags:
  - domain
  - law
  - okf
sources:
  - id: plan_md
    resource: /plan/plan.md
    title: e-Gov法令XMLのOpen Knowledge Format（OKF）準拠Markdown変換計画
---

# 法令 XML から OKF Markdown への変換仕様

## 1. 概要

総務省・デジタル庁の「法令標準 XML スキーマ v3」に基づき、法令テキストの完全 ASIS（原本維持）を守りつつ、LLM/RAG および Web ビューワーに最適化された OKF (Open Knowledge Format) 形式へ決定論的に変換する。

## 2. 構造マッピング

- **フォルダ命名**: 原則「法令タイトルのみ（最大20文字）」の極短構成。バージョン重複時は `_2`, `_3` の最小連番。
- **ファイル名サニタイズ**: OS 禁止文字 (`:\/*?"<>|`) はすべてハイフン `-` に自動置換（例: `art_436-448...md`）。
- **1条文 = 1ファイル**: `articles/art_001_第一条.md`
- **完全インデックスツリー**:
  - ルート `index.md`: 全法令の最上位ポータル
  - 法令トップ `index.md`: 各法令の総合目次
  - サブインデックス `articles/index.md`, `suppl/index.md`, `appendix/index.md`: 各ディレクトリの 404 防止用インデックス
- **附則の集約**: `suppl/suppl_main.md`（制定時附則）、`suppl/suppl_amendments.md`（全沿革・改正附則一覧）
- **別表・様式の個別/集約分離**:
  - `appendix/table_001_別表第一.md`（独立保持）
  - `appendix/appdx_styles.md`（極小様式等の集約結合）

## 3. ASIS 維持ルール & メタデータ補完

- **ルビ**: `<Ruby>/<Rt>` の親文字のみを保持し、読みは非破壊除去。
- **表**: 結合なしは GFM パイプテーブル、`rowspan`/`colspan` を含む表は HTML `<table>`。
- **数式**: `<ArithFormula>` は LaTeX `$ ... $` 表記。
- **CSV メタデータ統合**: ZIP 内に含まれるすべての CSV（`1.csv`, `2.csv` ... や `20.csv` などの連番・複数 CSV）を自動探索・マージし、`title_kana`, `promulgate_date`, `enforce_date`, `amend_law_title`, `amend_law_num`, `is_unexecuted` を YAML Frontmatter に自動補完。
