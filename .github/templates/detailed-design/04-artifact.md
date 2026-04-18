---
doc-type: artifact
doc-kind: master
phase: detailed-design
process: 4
iteration: 1
version: "1.0"
status: draft
input-refs:
  - path: "docs/detailed-design/03-decisions.md"
    version: "1.0"
  - path: "docs/basic-design/04-artifact.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: false
---

# ④ 詳細設計書（API仕様・DBスキーマ・テストケース設計） — 詳細設計

> **用途**: ③承認済みの方針に基づき、API仕様・DBスキーマ・テストケースを詳細に定義する。
> **TDD**: テストケース設計書はこのフェーズで作成し、実装フェーズではこれを先行して実装（Red）する。

---

## API仕様

### 共通仕様

| 項目 | 内容 |
|------|------|
| ベースURL | `https://api.example.com/v1` |
| 認証方式 | Bearer Token（JWT） / その他 |
| レスポンス形式 | JSON |
| 文字コード | UTF-8 |
| エラーレスポンス形式 | `{"code": "ERR_XXX", "message": "...", "details": [...]}` |

### エンドポイント一覧

| API-ID | エンドポイント | メソッド | 概要 | 認証 | 対応要件 |
|--------|-------------|---------|------|-----|---------|
| API-001 | `/resources` | GET | リソース一覧取得 | 要 | REQ-F-001 |

### エンドポイント詳細

#### API-001: [エンドポイント名]

**リクエスト**

```
GET /api/v1/resources
Authorization: Bearer <token>
```

| パラメータ | 場所 | 型 | 必須 | 説明 | バリデーション |
|-----------|------|---|------|-----|-------------|
| page | Query | integer | 任意 | ページ番号（1〜） | min:1 |

**レスポンス**: `200 OK`

```json
{
  "data": [],
  "meta": { "total": 0, "page": 1, "per_page": 20 }
}
```

**エラーレスポンス**

| HTTPステータス | コード | 説明 |
|-------------|-------|------|
| 400 | ERR_VALIDATION | バリデーションエラー |
| 401 | ERR_UNAUTHORIZED | 認証失敗 |
| 404 | ERR_NOT_FOUND | リソース未発見 |

---

## DBスキーマ

### ER図（テキスト表現）

```
[users] 1 ─── N [orders] 1 ─── N [order_items]
                                        │
                               N ───── 1 [products]
```

### テーブル定義

#### テーブル: `table_name`

```sql
CREATE TABLE table_name (
    id          BIGSERIAL PRIMARY KEY,
    -- フィールド定義
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
```

| カラム名 | 型 | NULL | デフォルト | 説明 | インデックス |
|---------|---|------|----------|------|-----------|
| id | BIGINT | NOT NULL | AUTO | PK | PK |

### インデックス方針

| テーブル | インデックス | 対象カラム | 種別 | 理由 |
|---------|-----------|---------|------|------|
| | | | BTREE / HASH | |

### マイグレーション方針

- ツール:（例: Flyway / Liquibase / Alembic）
- 命名規則: `V{version}__{description}.sql`

---

## ドメインモデル / DTO 定義

### エンティティ: `EntityName`

| フィールド | 型 | 必須 | バリデーション | 説明 |
|-----------|---|------|-------------|------|
| id | UUID | Yes | | |

---

## テストケース設計書（TDD先行）

> このテストケースは実装フェーズで **Red（テスト先行作成）** として使用する。

### ユニットテストケース

| TC-ID | テストクラス | テスト関数名 | テスト内容 | 入力 | 期待出力 / 期待動作 | 対応要件 |
|-------|-----------|-----------|---------|------|----------------|---------|
| TC-U-001 | | `test_xxx_正常系` | | | | REQ-F-001 |
| TC-U-002 | | `test_xxx_異常系` | | | 例外スロー | |

### インテグレーションテストケース

| TC-ID | テスト対象フロー | テスト内容 | 前提条件・フィクスチャ | 期待レスポンス | 対応要件 |
|-------|--------------|---------|----------------|------------|---------|
| TC-I-001 | | | | HTTP 200 | |

### テストカバレッジ目標

| テストレベル | 対象 | 目標カバレッジ |
|-----------|------|------------|
| ユニット | ビジネスロジック層 | 80% 以上 |
| インテグレーション | APIエンドポイント | 全エンドポイント |

---

## セキュリティ設計

| 脅威カテゴリ（OWASP Top10） | 対策 | 実装箇所 |
|--------------------------|------|---------|
| インジェクション（A03） | パラメータ化クエリ | DB層 |
| 認証の失敗（A07） | JWT + リフレッシュトークン | 認証サービス |
| IDOR（A01） | 認可チェック | APIミドルウェア |

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|---------|------|---------|--------|
| 1.0 | YYYY-MM-DD | 初版作成 | |
