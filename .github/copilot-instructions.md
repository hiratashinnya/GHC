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
|------|------|
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
|--------------|------|
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
2. 各プロンプトに日本語のREADMEを添えること