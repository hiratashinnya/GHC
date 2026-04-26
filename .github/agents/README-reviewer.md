# reviewer エージェント

## 概要

GitHub Copilot カスタマイズファイル（Agents / Skills / Hooks / Prompts / Instructions）のレビュー・検証・デバッグ専門エージェントです。読み取り専用で動作し、問題点と修正案のみを報告します。

## 役割

- YAML フロントマターの構文・規約違反を検出する
- `name` フィールドがファイル名（またはフォルダ名）と一致しているか検証する
- `description` にトリガーワードが含まれているか確認する
- `tools` の過剰指定（swiss-army アンチパターン）を指摘する
- Skill の手順・Agent の制約記述の欠落を検出する
- 言語・ツール制約違反（非標準パッケージ等）を発見する

## 制約事項

- DO NOT ファイルを編集する（読み取り専用）
- DO NOT `.github/` 配下以外のファイルを対象にする
- 問題点の報告と修正案の提示のみを行う

## 起動パターン

```
# 単一ファイルのレビュー
@reviewer .github/agents/orchestrator.agent.md をレビューして

# スキル全体の検証
@reviewer .github/skills/ 配下を全部チェックして

# フロントマターのみ確認
@reviewer このエージェントのフロントマターに問題ないか確認して
```

## 出力形式

問題点を箇条書きで列挙し、各問題に具体的な修正案を提示する。問題がない場合は「✅ 問題なし」と報告する。

## 関連ファイル

| ファイル | 役割 |
| --------- | ------ |
| `.github/agents/reviewer.agent.md` | このエージェントの定義（英語） |
| `.github/copilot-instructions.md` | YAML フロントマター規約の一次ソース |
