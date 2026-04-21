---
doc-type: artifact
doc-kind: master
phase: detailed-design
process: 4
layer: "L3"
artifact-type: api
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

# ④ API仕様 — {compId}

> **用途**: コンポーネント `{compId}` のAPIエンドポイント詳細仕様。

---

## エンドポイント一覧

| API-ID | エンドポイント | メソッド | 概要 | 認証 | 対応要件 |
|--------|-------------|---------|------|-----|---------|
| API-001 | `/resources` | GET | リソース一覧取得 | 要 | REQ-F-001 |

---

## エンドポイント詳細

### API-001: {エンドポイント名}

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

## 変更履歴

| バージョン | 日付 | 変更内容 | 変更者 |
|---------|------|---------|--------|
| 1.0 | YYYY-MM-DD | 初版作成 | |
