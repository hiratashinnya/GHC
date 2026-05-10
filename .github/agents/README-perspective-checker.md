# perspective-checker エージェント README

## 概要

`perspective-checker` は、`adversarial.agent` から呼び出される**単観点敵対的検証専門サブエージェント**です。1回の呼び出しで1つの観点（`perspectives/` 配下のセクション）のみを担当し、完全に独立したコンテキストで草案を批判的に分析します。

複数の `perspective-checker` が並列的に異なる観点で同一草案を検証することで、単一エージェントによる「自己強化バイアス」（自分が作った草案を高評価しがちな傾向）を排除します。

## 直接呼び出しについて

このエージェントは**ユーザーが直接呼び出すことを想定していません**。`@adversarial` 経由で自動的に呼び出されます。

## 観点ファイルとの関係

```
.github/perspectives/
  customization.md          ← .github/ ファイルの形式・構造観点（P-CUS-01〜05）
  prevent-recurrence.md     ← 再発防止策の意味・効果・整合性観点（P-PR-01〜05）
```

各セクション（例: `P-PR-01`）が1回の `perspective-checker` 呼び出しに対応します。`adversarial.agent` は必要な観点セクションごとにサブエージェントを生成します。

## アーキテクチャ上の位置づけ

```
prevent-recurrence.agent
    └─ adversarial.agent（Stage V コーディネーター）
           ├─ perspective-checker（P-CUS-01）← 独立コンテキスト
           ├─ perspective-checker（P-CUS-02）← 独立コンテキスト
           ├─ perspective-checker（P-PR-01） ← 独立コンテキスト
           ├─ perspective-checker（P-PR-02） ← 独立コンテキスト
           └─ ... （観点数分）
```

## ツール

| ツール | 用途 |
|--------|------|
| `read` | 観点ファイル・草案ファイルの読み込み |
| `search` | 既存ファイルとの重複・矛盾確認 |

**編集ツールは持ちません。このエージェントは読み取り専用です。**

## 出力

構造化されたチェック結果レポート（Markdown）を呼び出し元の `adversarial.agent` に返します。各指摘には Lv1/Lv2/Lv3 の仮判定が付与されます。最終的な Lv 確定は `adversarial.agent` の Stage V3 で `severity-triage` スキルが行います。
