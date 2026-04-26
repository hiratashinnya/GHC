---
doc-type: decision
doc-kind: master
phase: PHASE_NAME
process: 3
iteration: 0
version: "1.0"
status: awaiting-approval
input-refs:
  - path: "02-breakdown.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: true
tags: []
---

# ③ 意思決定・検討 — [PHASE_DISPLAY_NAME]

> **用途**: ②分解結果を入力として、方針・アーキテクチャ・アルゴリズム等の選択肢をAIが提案し、人間が承認する。
> **⚠️ フェーズゲート**: このドキュメントが `status: approved` になるまで④成果物の作成に進めない。

---

## 意思決定サマリ

| 決定項目 | 選択結果 | 承認状態 |
| --------- | --------- | --------- |
| 項目1 | | ⏳ awaiting |
| 項目2 | | ⏳ awaiting |

---

## 決定項目の詳細検討

### 決定項目 1: [タイトル]

**背景・課題**:

**選択肢**:

| 選択肢 | メリット | デメリット | 適用条件 |
| -------- | --------- | ----------- | --------- |
| A: | | | |
| B: | | | |

**AI推奨**: 選択肢X — 理由: ...

**決定**: <!-- 人間が記入 -->

**根拠**: <!-- 人間が記入 -->

---

### 決定項目 2: [タイトル]

（同上の構造で記載）

---

## 未解決事項・リスク

- 項目1:
- 項目2:

---

## 承認セクション

<!-- 人間ゲート: 以下を記入して status を "approved" に変更してください -->

承認者: <!-- approved-by フィールドにも記入 -->
承認日: <!-- updated-at フィールドにも記入 -->
コメント:
