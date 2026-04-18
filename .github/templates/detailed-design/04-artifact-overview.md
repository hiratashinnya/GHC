---
doc-type: artifact
doc-kind: master
phase: detailed-design
process: 4
layer: "L1"
iteration: 1
version: "1.0"
status: draft
input-refs:
  - path: "docs/detailed-design/03-decisions-overview.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: false
---

# ④ 詳細設計 全体サマリ（コンポーネント横断） — 詳細設計

> **用途**: 全コンポーネント横断の設計サマリ。共通仕様・コンポーネント間インタフェース・セキュリティ設計をここに集約する。
> 各コンポーネントの詳細は `components/{compId}/04-artifact-{compId}.md` を参照。

---

## 共通仕様

| 項目 | 内容 |
|------|------|
| ベースURL | `https://api.example.com/v1` |
| 認証方式 | Bearer Token（JWT） / その他 |
| レスポンス形式 | JSON |
| 文字コード | UTF-8 |
| エラーレスポンス形式 | `{"code": "ERR_XXX", "message": "...", "details": [...]}` |

---

## コンポーネント設計ファイルリンク

| COMP-ID | コンポーネント名 | サマリ | API | Schema | Domain | TestCase | ステータス |
|---------|-------------|-------|-----|--------|--------|----------|-----------|
| COMP-001 | | [サマリ](components/COMP-001/04-artifact-COMP-001.md) | [API](components/COMP-001/04-artifact-COMP-001-api.md) | [Schema](components/COMP-001/04-artifact-COMP-001-schema.md) | [Domain](components/COMP-001/04-artifact-COMP-001-domain.md) | [TestCase](components/COMP-001/04-artifact-COMP-001-testcase.md) | ─ |

---

## コンポーネント間インタフェース

| IF-ID | 呼び出し元 | 呼び出し先 | プロトコル | 概要 |
|-------|----------|----------|----------|------|
| IF-001 | COMP-001 | COMP-002 | REST / gRPC / Event | |

---

## セキュリティ設計（横断）

| 脅威カテゴリ（OWASP Top10） | 対策 | 実装箇所 |
|--------------------------|------|---------|
| インジェクション（A03） | パラメータ化クエリ | DB層 |
| 認証の失敗（A07） | JWT + リフレッシュトークン | 認証サービス |
| IDOR（A01） | 認可チェック | APIミドルウェア |

---

## マイグレーション方針

- ツール:（例: Flyway / Liquibase / Alembic）
- 命名規則: `V{version}__{description}.sql`

---

## テストカバレッジ目標（全体）

| テストレベル | 対象 | 目標カバレッジ |
|-----------|------|------------|
| ユニット | ビジネスロジック層 | 80% 以上 |
| インテグレーション | APIエンドポイント | 全エンドポイント |

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|---------|------|---------|--------|
| 1.0 | YYYY-MM-DD | 初版作成 | |
