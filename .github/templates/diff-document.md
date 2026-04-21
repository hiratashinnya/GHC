---
doc-type: PROCESS_TYPE
doc-kind: diff
phase: PHASE_NAME
process: PROCESS_NUM
iteration: ITER_NUM
version: "1.0"
status: draft
base-version: "MASTER_VERSION"
input-refs:
  - path: "docs/PHASE_NAME/PREV_DOC.md"
    version: ""
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approval-required: false
tags: []
---

# [差分] ① / ② / ③ / ④ / ⑤ [PROCESS_DISPLAY_NAME] — [PHASE_DISPLAY_NAME] / iter[N]

> **差分ドキュメントの用途**:
> 当該イテレーション・フェーズの変更点・追加事項のみを記載する。
> 正本（`docs/<phase>/0N-*.md`）へのマージ後に正本の `version` をインクリメントする。
>
> **配置先**: `iter/iterN/phaseX/0N-<type>.md`（`docs/` ツリーには含めない）

---

## 変更サマリ

| 変更種別 | 対象 | 説明 |
|---------|------|------|
| 追加 | | |
| 変更 | | |
| 削除 | | |

**正本バージョン（マージ前）**: `base-version` フィールド参照
**正本バージョン（マージ後想定）**: 手動でインクリメント

---

## 差分内容

<!-- このイテレーション・フェーズで追加・変更・削除する内容のみ記載 -->
<!-- 変更点を明確にするため、変更前→変更後 の形式で記述することを推奨 -->

### 追加事項

（なし / または内容を記載）

### 変更事項

（なし / または変更前→変更後を記載）

### 削除事項

（なし / または削除内容と理由を記載）

---

## 正本マージ後のアクション

- [ ] `docs/<phase>/0N-*.md` に差分内容を反映
- [ ] 正本の `version` をインクリメント
- [ ] 正本の `updated-at` を更新
- [ ] 正本の `status` を `approved` に設定
- [ ] `docs/dashboard.md` のステータスマトリクスを更新

---

## 承認セクション（approval-required: true の場合のみ）

<!-- ③ decisions または ⑤ verification の差分の場合は approval-required: true に変更 -->

承認者:
承認日:
コメント:
