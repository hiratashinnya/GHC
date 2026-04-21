---
doc-type: artifact
doc-kind: master
phase: detailed-design
process: 4
layer: "L3"
artifact-type: testcase
component-id: "{compId}"
iteration: 1
version: "1.0"
status: draft
input-refs:
  - path: "docs/detailed-design/components/{compId}/04-artifact-{compId}.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: false
tags: []
---

# ④ テストケース設計 — {compId}

> **用途**: コンポーネント `{compId}` のテストケース設計書（TDD先行）。
> 実装フェーズではこのテストケースを **Red（テスト先行作成）** として使用する。

---

## テストケースサマリ

| テストレベル | ケース数 | カバー要件数 |
|-----------|--------|-----------|
| ユニット | 0 | 0 |
| インテグレーション | 0 | 0 |

---

## ユニットテストケース

| TC-ID | テストクラス | テスト関数名 | テスト内容 | 入力 | 期待出力 / 期待動作 | 対応要件 |
|-------|-----------|-----------|---------|------|----------------|---------|
| TC-U-001 | | `test_xxx_正常系` | | | | REQ-F-001 |
| TC-U-002 | | `test_xxx_異常系` | | | 例外スロー | |

---

## インテグレーションテストケース

| TC-ID | テスト対象フロー | テスト内容 | 前提条件・フィクスチャ | 期待レスポンス | 対応要件 |
|-------|--------------|---------|----------------|------------|---------|
| TC-I-001 | | | | HTTP 200 | |

---

## 要件 → テストケース トレーサビリティ

| 要件ID | テストケースID | テストレベル | カバー状態 |
|-------|------------|-----------|---------|
| REQ-F-001 | TC-U-001, TC-I-001 | Unit + Integration | ✅ |

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|---------|------|---------|--------|
| 1.0 | YYYY-MM-DD | 初版作成 | |
