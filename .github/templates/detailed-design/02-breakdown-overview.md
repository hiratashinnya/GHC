---
doc-type: breakdown
doc-kind: master
phase: detailed-design
process: 2
sub-process: "a"
iteration: 1
version: "1.0"
status: draft
input-refs:
  - path: "docs/detailed-design/01-validation.md"
    version: "1.0"
  - path: "docs/basic-design/04-artifact.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: false
---

# ②-a 全体分解（コンポーネント配分・トレーサビリティ） — 詳細設計

> **用途**: 基本設計のコンポーネント仕様（COMP-ID）を起点に、API・テーブル・ドメインモデル・テストケースの分解要素を各コンポーネントへ配分する。
> 詳細設計で独自にサブコンポーネントへ再分割する場合もここで定義する。

---

## コンポーネント配分マトリクス

> `basic-design/04-artifact.md` の COMP-ID を起点とし、各分解要素を割り当てる。

| COMP-ID | コンポーネント名 | API | テーブル | ドメインモデル | テストケース | サブコンポーネント |
|---------|-------------|-----|---------|------------|-----------|-------------|
| COMP-001 | | API-001, ... | TBL-001, ... | MDL-001, ... | TC-U-001, ... | ─ |

---

## 分解要素サマリ

| 分類 | 要素数 | メモ |
|------|--------|------|
| APIエンドポイント | 0 | |
| DBテーブル | 0 | |
| ドメインモデル / DTO | 0 | |
| テストケース（ユニット） | 0 | |
| テストケース（インテグレーション） | 0 | |

---

## サブコンポーネント定義（任意）

> 基本設計のCOMP-IDをさらに細分化する場合にここで定義する。

| サブCOMP-ID | 親COMP-ID | サブコンポーネント名 | 責務 |
|------------|---------|----------------|------|
| | | | |

---

## 要件トレーサビリティ

| 要件ID | COMP-ID | API-ID | TBL-ID | TC-ID |
|-------|---------|--------|--------|-------|
| REQ-F-001 | COMP-001 | API-001 | TBL-001 | TC-U-001 |

---

## ③意思決定プロセスへの論点

- 論点1:
- 論点2:

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|---------|------|---------|--------|
| 1.0 | YYYY-MM-DD | 初版作成 | |
