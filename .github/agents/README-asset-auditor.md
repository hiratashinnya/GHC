# asset-auditor エージェント

## 概要

新しいスキル・エージェント・コードを作成する**前に**、既存資産の棚卸しを行い、**重複・矛盾・競合**と「新規作成 vs 既存変更」の推奨を返す**読み取り専用の監査者**。

ファイルは一切編集しない。

> `spec-inspector` との違い: こちらは「**資産そのもの**（既存スキル・エージェント・手順・コード）」の重複/競合監査。`spec-inspector` は「**仕様**（I/O台帳・イベント・DFD）」の整合点検。

## 起動トリガー

```
@asset-auditor <新資産の説明>
```

## 出力

- 既存資産一覧（`name | 種別 | 責務`）
- 新資産ごとの表：`重複 | 矛盾 | 競合 | 推奨(新規/変更) | 根拠`
- `description` 差別化案
- 同期更新が必要な台帳/規約のリスト

## 関連ファイル

| ファイル | 役割 |
|---------|------|
| `.github/agents/asset-auditor.agent.md` | エージェント定義 |
| `.claude/agents/asset-auditor.md` | Claude Code 版 |
| `.github/agents/README-tailoring-registry.md` | テーラリング台帳 |
