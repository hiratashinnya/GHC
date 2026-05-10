# adversarial エージェント README

## 概要

`adversarial` は、`prevent-recurrence.agent` の Stage 4（防止策草案作成）と Stage 5（人間承認）の間で自動実行される**3段階敵対的検証パイプライン**エージェントです。

「AIが作ったルールをAIが批判的に検証する」アーキテクチャにより、人間が全量レビューしなくても一定品質の草案のみが Stage 5 に到達するようにします。

## 処理パイプライン

```
[呼び出し元: prevent-recurrence.agent]
    │
    ▼
Stage V1: 静的・形式的検証
  ├─ YAML 構文 / 必須フィールド / 名前整合
  ├─ 禁止パッケージ / 曖昧表現 / 重複ルール
  └─ → Lv1 を即時自動修正

Stage V2: 批判的多角検証（サブエージェント群）
  ├─ perspective-checker（P-CUS-01）← 独立コンテキスト
  ├─ perspective-checker（P-CUS-02）← 独立コンテキスト
  ├─ perspective-checker（P-CUS-03）← 独立コンテキスト
  ├─ perspective-checker（P-CUS-04）← 独立コンテキスト
  ├─ perspective-checker（P-CUS-05）← 独立コンテキスト
  ├─ perspective-checker（P-PR-01）← 独立コンテキスト
  ├─ perspective-checker（P-PR-02）← 独立コンテキスト
  ├─ perspective-checker（P-PR-03）← 独立コンテキスト
  ├─ perspective-checker（P-PR-04）← 独立コンテキスト
  └─ perspective-checker（P-PR-05）← 独立コンテキスト

Stage V3: 集約・severity-triage・レポート
  ├─ 重複指摘の除去・統合
  ├─ severity-triage スキルで最終 Lv 確定
  └─ → 構造化レポートを prevent-recurrence.agent に返す
    │
    ▼
[呼び出し元: prevent-recurrence.agent Stage 5 へ]
```

## Lv 判定と対応

| Lv | 判定 | 対応 |
|----|------|------|
| **Lv1** | 客観的・ルールベース | 自動修正＋ログ記録 |
| **Lv2** | 方針・設計関連 | 修正素案生成 → Stage 5 で人間承認 |
| **Lv3** | トレードオフ・戦略判断 | 選択肢提示 → Stage 5 を事実上ブロック |

## 使用するファイル

| ファイル | 役割 |
|----------|------|
| `.github/perspectives/customization.md` | `.github/` ファイルの形式・構造観点（P-CUS-01〜05） |
| `.github/perspectives/prevent-recurrence.md` | 再発防止策の意味・効果・整合性観点（P-PR-01〜05） |
| `.github/skills/severity-triage/SKILL.md` | Lv 最終判定ロジック |
| `.github/agents/perspective-checker.agent.md` | 単観点サブエージェント |

## 観点の拡張

新しい検証対象（例: フェーズ別成果物、テストケース等）には `perspectives/` に新しいファイルを追加するだけで対応できます。`adversarial.agent` 本体を修正する必要はありません。

## ツール

| ツール | 用途 |
|--------|------|
| `read` | 草案・観点ファイルの読み込み |
| `search` | 重複・整合性確認 |
| `edit` | Lv1 自動修正のみ |
| `todo` | 対応アクションのトラッキング |
| `agent` | perspective-checker サブエージェントの呼び出し |

## 直接呼び出しについて

このエージェントはユーザーが直接呼び出すことを想定していません。`prevent-recurrence.agent` が Stage 4 完了後に自動的に呼び出します。
