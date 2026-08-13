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

- **1条文 = 1ファイル**: `articles/art_001_第一条.md`
- **目次**: `index.md` (各条文の件名 `第一条（目的）` を表示)
- **附則**: `suppl/suppl_main.md`（制定時附則）、`suppl/suppl_amendments.md`（全沿革・改正附則一覧）
- **別表**: `appendix/table_001_別表第一.md`（独立保持）
- **様式・付録**: `appendix/appdx_styles.md`（集約結合）

## 3. ASIS 維持ルール

- **ルビ**: `<Ruby>/<Rt>` の親文字のみを保持し、読みは非破壊除去。
- **表**: 結合なしは GFM パイプテーブル、`rowspan`/`colspan` を含む表は HTML `<table>`。
- **数式**: `<ArithFormula>` は LaTeX `$ ... $` 表記。
