---
doc-type: artifact
doc-kind: master
phase: implementation
process: 4
iteration: 1
version: "1.0"
status: draft
input-refs:
  - path: "docs/implementation/03-decisions.md"
    version: "1.0"
  - path: "docs/detailed-design/04-artifact.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: false
---

# ④ 実装完了サマリ — 実装（TDD）

> **用途**: TDDサイクル完了後のコーディングタスク完了状況と `src/` への参照リストを記録する。
> コード本体は `src/` に配置しており、このドキュメントには**完了サマリと参照リストのみ**を記載する。

---

## 実装サマリ

| 項目 | 内容 |
|------|------|
| 実装完了タスク数 | N / N |
| ユニットテスト | N件 PASS / 0件 FAIL |
| インテグレーションテスト | N件 PASS / 0件 FAIL |
| コードカバレッジ | N% |
| 未解決の技術的負債 | N件 |

---

## コーディングタスク完了一覧

| TASK-ID | タスク名 | ステータス | TDDサイクル | コードレビュー | 参照先（`src/`） |
|---------|---------|-----------|-----------|------------|--------------|
| TASK-001 | 環境構築 | ✅ Done | — | ✅ Approved | `src/` |
| TASK-002 | DBマイグレーション | ✅ Done | — | ✅ Approved | `src/db/migrations/` |
| TASK-003 | エンティティ定義 | ✅ Done | Red→Green→Refactor | ✅ Approved | `src/domain/` |
| TASK-004 | サービス層 | ✅ Done | Red→Green→Refactor | ✅ Approved | `src/services/` |
| TASK-005 | APIコントローラ | ✅ Done | Red→Green→Refactor | ✅ Approved | `src/api/` |

---

## テスト結果サマリ

### ユニットテスト

| テストスイート | PASS | FAIL | SKIP | カバレッジ | カバレッジレポート |
|------------|------|------|------|---------|------|------------------|
| domain/ | 0 | 0 | 0 | 0% | [レポートへのリンク] |
| services/ | 0 | 0 | 0 | 0% | [レポートへのリンク] |
| api/ | 0 | 0 | 0 | 0% | [レポートへのリンク] |
| **合計** | **0** | **0** | **0** | **0%** | [レポートサマリへのリンク] |

### インテグレーションテスト

| テストスイート | PASS | FAIL | SKIP |
|------------|------|------|------|
| tests/integration/ | 0 | 0 | 0 |

---

## `src/` ディレクトリ構成

```
src/
  api/             # APIコントローラ / ハンドラ
  domain/          # ドメインモデル / エンティティ
  services/        # ビジネスロジック層
  repositories/    # データアクセス層
  db/
    migrations/    # DBマイグレーションファイル
  tests/
    unit/          # ユニットテスト
    integration/   # インテグレーションテスト
  config/          # 設定ファイル
```

---

## 技術的負債 / 未解決事項

| ID | 内容 | 重要度 | 対応予定イテレーション |
|----|------|--------|-----------------|
| TD-001 | | Low / Mid / High | iter2 |

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|---------|------|---------|
| 1.0 | YYYY-MM-DD | 初版（iter1 実装完了） |
