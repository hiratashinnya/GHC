---
name: copilot-instructions
description: "Workspace-level guidance for GitHub Copilot Chat. This repository builds and maintains an AI-driven development environment using GitHub Copilot Agents, Skills, Hooks, and Prompts."
---

# AI-Driven Development Environment

GitHub Copilot を活用した AI 駆動開発のための環境リポジトリ。Agents・Skills・Hooks・Prompts を整備し、Copilot との協働ワークフローを体系化・自動化する。

## ディレクトリ構造

```
.github/
  copilot-instructions.md     # ワークスペース指示（このファイル）
  agents/    *.agent.md       # カスタムエージェント
  skills/    <name>/SKILL.md  # オンデマンドスキル
  hooks/     *.json           # ライフサイクルフック設定
             scripts/         # フックが呼び出すスクリプト
  prompts/   *.prompt.md      # 再利用可能プロンプト
```

## 言語・ツール制約

| 許可 | 禁止 |
| ------ | ------ |
| Markdown, YAML | その他のマークアップ・設定言語 |
| Python（標準ライブラリ + Copilot SDK） | 非標準 Python パッケージ |
| PowerShell（組み込みコマンドレットのみ） | 外部 PowerShell モジュール |

## YAML フロントマター規約

- `description` は **必須**。`"Use when... trigger phrases"` 形式でトリガーワードを含める
- コロンを含む場合は引用符で囲む（例: `description: "Use when: doing X"`）
- `name` はファイル名（拡張子除く）またはスキルのフォルダ名と一致させる
- `tools` は必要最小限に絞る（未指定 = デフォルトツール）

## カスタマイズの追加方法

| 追加したいもの | 方法 |
| -------------- | ------ |
| Agent | `@scaffold` に依頼 または `/create-agent` |
| Skill | `@scaffold` に依頼 または `/create-skill` |
| Hook | `@scaffold` に依頼 または `/create-hook` |
| Prompt | `@scaffold` に依頼 または `/create-prompt` |

既存ファイルのレビュー・検証は `@reviewer` エージェントを使用する。

## Hooks作成時のルール

1. Hooks用スクリプトには必ずデバッグ用機能を実装すること
2. デバッグ用機能は有効無効を設定用のファイルのパスの存在有無で切り替えられるようにすること
3. デバッグ用機能は、Hooksが実行された際に入出力情報やその他デバッグに必要な変数などの情報がログファイルに記録されるようにすること

## 開発の進め方

1. 新しいワークフローを自動化したい → `@scaffold` に目的を説明する
2. 既存 customization をデバッグしたい → `@reviewer` に対象ファイルを渡す
3. 繰り返し使うタスクを定型化したい → `/create-prompt` でプロンプトを作成する

## 順守事項

1. プロンプトは英語で記載すること
2. 各プロンプト、SKILL.md、agent.md に日本語のREADMEを添えること
3. 作業前に必ず計画を立て、ダッシュボードまたはplan-systemDevWorkflow.prompt.mdにTODO形式で記録すること
4. 作業着手前、作業完了後は必ずダッシュボードまたはplan-systemDevWorkflow.prompt.mdの該当項目のステータスを更新すること
5. 明示的に指示されない限りリファクタリングはしないこと。必要な場合はまず人間に提案し、承認を得てから行うこと。
6. テスト結果（testresult.md）を記録・更新する際は、実施日（`実行日:`）に加えてコミットID（`コミットID:`）を必ず記載すること。コミットIDは `git log --oneline -1` で取得する。
7. テスト作業の実施順序を厳守すること。**testcase.md（仕様）→ テストコード実装 → コミット → テスト実行 → testresult.md 記録** の順序を逆にしてはならない。テスト実行前にコミットしていない場合は、まずコミットしてからテストを実行すること。testcase.md をテスト後に辻褄合わせで更新することは禁止。
8. テスト失敗は隠蔽しないこと。`testresult.md` には実行結果をそのまま記録し、FAIL がある場合は最低限「備考付きサマリ（失敗行の注記）」と「失敗詳細（期待値/実際値/原因/次アクション）」を記載すること。
