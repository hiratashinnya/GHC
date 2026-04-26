# dashboard-sync スキル

## 概要

`docs/dashboard.md` を各フェーズのドキュメント実態と同期するスキル。フロントマターの `status` フィールドを走査し、ステータスマトリクス・コンポーネント別進捗・ボトルネック・次アクションを更新する。

## 使い方

```
/dashboard-sync requirements
/dashboard-sync detailed-design
/dashboard-sync implementation
```

引数にフェーズ名を指定する: `requirements` | `basic-design` | `detailed-design` | `implementation` | `testing` | `release`

## 主な機能

- 全6フェーズに対応（1スキルに統合、引数でフェーズ指定）
- ステータスマトリクスの自動更新
- 詳細設計フェーズのコンポーネント別進捗テーブル更新
- ボトルネック検出と表示
- 次アクションの自動推奨
- イテレーション履歴の管理

## フェーズ別の追加チェック

| フェーズ | 追加チェック内容 |
| --------- | --------------- |
| requirements | イテレーション別スコープファイルの存在確認 |
| basic-design | コンポーネント仕様の完成度 |
| detailed-design | ②v列 + コンポーネント別進捗テーブル |
| implementation | タスク消化率 + テストパス率 |
| testing | 品質ゲート充足状況 |
| release | デプロイ結果 + スモークテスト結果 |
