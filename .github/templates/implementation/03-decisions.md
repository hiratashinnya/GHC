---
doc-type: decision
doc-kind: master
phase: implementation
process: 3
iteration: 1
version: "1.0"
status: awaiting-approval
input-refs:
  - path: "docs/implementation/02-breakdown.md"
    version: "1.0"
created-at: "YYYY-MM-DD"
updated-at: "YYYY-MM-DD"
approved-by: null
approved-at: "YYYY-MM-DD"
approval-required: true
---

# ③ 意思決定・検討 — 実装（TDD）

> **用途**: コーディングタスクリストを基に、実装順序・リファクタリング方針・コードレビュー方針をAIが提案し、人間が承認する。
> **⚠️ フェーズゲート**: このドキュメントが `status: approved` になるまでコーディング（TDDサイクル）を開始しない。

---

## 意思決定サマリ

| 決定項目 | 選択結果 | 承認状態 |
|---------|---------|---------|
| 実装順序・並列化方針 | | ⏳ awaiting |
| リファクタリング方針 | | ⏳ awaiting |
| コードレビュー粒度 | | ⏳ awaiting |
| ブランチ戦略 | | ⏳ awaiting |

---

## 決定項目 1: 実装順序・並列化方針

**AI提案の実装順序**: TASK-001 → TASK-002 → ...

**並列化可能なタスク**:
- TASK-XXX と TASK-YYY は依存関係がないため並列実行可能

**決定**: <!-- 人間が記入 -->
（変更がある場合は `02-breakdown.md` のタスク一覧も更新すること）

---

## 決定項目 2: リファクタリング方針

| 方針 | 詳細 |
|------|------|
| タイミング | Green 直後 / フィーチャー完了後 / スプリント末 |
| 対象基準 | コードの重複 / 関数の長さ（20行超） / 複雑度（循環複雑度 10超） |
| リファクタ禁止条件 | テスト全パス前 |
**AI推奨**: 選択肢X — 理由: ...
**決定**: <!-- 人間が記入 -->

---

## 決定項目 3: コードレビュー粒度

| 選択肢 | 説明 |
|--------|------|
| A: タスク単位（PR per task） | 細かくレビューできる・PRが多い |
| B: フィーチャー単位（PR per feature） | レビュー負荷が低い・差分が大きめ |
| C: 日次バッチ | 作業とレビューのリズムが明確 |

**AI推奨**: 選択肢X — 理由: ...
**決定**: <!-- 人間が記入 -->

---

## 決定項目 4: ブランチ戦略

| 選択肢 | 説明 |
|--------|------|
| A: GitHub Flow（main + feature/xxx） | シンプル・継続デプロイ向き |
| B: Git Flow（main / develop / feature / release） | リリース管理が明確 |
| C: Trunk-Based Development | 小さなPR頻繁マージ |

**AI推奨**: 選択肢X — 理由: ...
**決定**: <!-- 人間が記入 -->

---

## 未解決事項・リスク

| ID | 内容 | 対応方針 |
|----|------|--------|
| RISK-IMP-001 | | |

---

## 承認セクション

承認者:
承認日:
コメント:
