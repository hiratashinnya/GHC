---
doc-type: verification
doc-kind: master
phase: detailed-design
process: 5
layer: "L2"
component-id: "{compId}"
iteration: 1
version: "1.0"
status: draft
input-refs:
  - path: "docs/detailed-design/components/{compId}/04-artifact-{compId}.md"
    version: "1.0"
  - path: "docs/detailed-design/components/{compId}/04-artifact-{compId}-api.md"
    version: "1.0"
  - path: "docs/detailed-design/components/{compId}/04-artifact-{compId}-schema.md"
    version: "1.0"
  - path: "docs/detailed-design/components/{compId}/04-artifact-{compId}-domain.md"
    version: "1.0"
  - path: "docs/detailed-design/components/{compId}/04-artifact-{compId}-testcase.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: false
tags: []
---

# ⑤ コンポーネント別検証 — {compId}

> **用途**: コンポーネント `{compId}` のAPI仕様・DBスキーマ・テストケースを検証する。
> 全体検証は `05-verification-overview.md` に集約される。

---

## 検証サマリ

| 検証軸 | 結果 | 備考 |
|--------|------|------|
| API仕様の完全性 | ✅ / ⚠️ / ❌ | |
| DBスキーマの整合性 | ✅ / ⚠️ / ❌ | |
| ドメインモデルの整合性 | ✅ / ⚠️ / ❌ | |
| テストケースの網羅性 | ✅ / ⚠️ / ❌ | |
| 実装可能性 | ✅ / ⚠️ / ❌ | |

**AI判定**: PASS / CONDITIONAL PASS / FAIL

---

## 品質基準チェックリスト

### API仕様

- [ ] 全APIエンドポイントにリクエスト・レスポンス形式が定義されている
- [ ] 全エンドポイントにエラーレスポンスが定義されている
- [ ] バリデーションルールが記述されている
- [ ] 認証・認可の要否が全エンドポイントに設定されている

### DBスキーマ

- [ ] 全テーブルにPK・作成日時・更新日時が設定されている
- [ ] 外部キー制約が適切に設定されている
- [ ] インデックス方針が記述されている

### テストケース（TDD）

- [ ] 全機能要件に対して正常系テストケースがある
- [ ] 主要な異常系・境界値テストケースがある
- [ ] テスト関数名がテスト内容を明示している

---

## 要件 → テストケース トレーサビリティ

| 要件ID | テストケースID | テストレベル | カバー状態 |
|-------|------------|-----------|---------|
| REQ-F-001 | TC-U-001, TC-I-001 | Unit + Integration | ✅ |

---

## 指摘事項

| ID | 重要度 | 対象箇所 | 指摘内容 | 対応方針 | ステータス |
|----|--------|---------|---------|---------|-----------|
| V-001 | High / Mid / Low | | | | Open / Resolved |

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|---------|------|---------|--------|
| 1.0 | YYYY-MM-DD | 初版作成 | |
