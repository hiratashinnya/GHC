# hooks-dev スキル

VS Code 向け GitHub Copilot エージェントフックの開発・デバッグを支援するスキル。

## 概要

このスキルは、以下のような作業を行う際に Copilot が自動的に参照する知識ベースです。

- 新しいフックスクリプト（`.py`）と JSON 設定ファイルの作成
- 既存フックスクリプトのデバッグ・修正
- フックイベント別のペイロードスキーマの確認
- ブロック・承認パターンの選択（exit code 2、permissionDecision deny/ask、continue: false など）
- `HookDebugLogger` を使ったデバッグログの追加

---

## ファイル構成

```text
.github/skills/hooks-dev/
  SKILL.md      ← Copilot が参照する英語の知識ベース（本スキルの本体）
  README.md     ← このファイル（日本語概要）
```

---

## 関連ドキュメント

| ドキュメント | 内容 |
| --- | --- |
| [`Hooks-instructions.md`](../Hooks-instructions.md) | アーキテクチャ概要・共通フィールド・exit code 表・スパイフック |
| [`hooks-docs/payload-PreToolUse.md`](../hooks-docs/payload-PreToolUse.md) | PreToolUse の入出力スキーマ・ブロックパターン |
| [`hooks-docs/payload-PostToolUse.md`](../hooks-docs/payload-PostToolUse.md) | PostToolUse の入出力スキーマ・後処理パターン |
| [`hooks-docs/payload-UserPromptSubmit.md`](../hooks-docs/payload-UserPromptSubmit.md) | プロンプト傍受・監査ログ |
| [`hooks-docs/payload-SessionStart.md`](../hooks-docs/payload-SessionStart.md) | セッション初期化・コンテキスト注入 |
| [`hooks-docs/payload-Stop.md`](../hooks-docs/payload-Stop.md) | セッション終了・後処理・無限ループ防止 |
| [`hooks-docs/payload-SubagentStart.md`](../hooks-docs/payload-SubagentStart.md) | サブエージェント起動・コンテキスト注入 |
| [`hooks-docs/payload-SubagentStop.md`](../hooks-docs/payload-SubagentStop.md) | サブエージェント完了・結果検証 |
| [`hooks-docs/payload-PreCompact.md`](../hooks-docs/payload-PreCompact.md) | 圧縮前の状態保存 |
| [`hooks-docs/tool-input-schema.md`](../hooks-docs/tool-input-schema.md) | 全ツールの tool_input スキーマ・読み書き分類表 |
| [`hooks-docs/hook-template.md`](../hooks-docs/hook-template.md) | チェックリスト・Python テンプレート・ブロックパターン集 |
| [`hooks/scripts/core/hook_payload.py`](../hooks/scripts/core/hook_payload.py) | facade: `get_hook_input()` / `get_hook_input_as()` / 互換 re-export |
| [`hooks/scripts/core/hook_input.py`](../hooks/scripts/core/hook_input.py) | `read_payload()` / `get_hook_input()` / `get_hook_input_as()` |
| [`hooks/scripts/core/hook_event.py`](../hooks/scripts/core/hook_event.py) | 全 8 イベント分型データクラス / `parse_payload()` |
| [`hooks/scripts/core/hook_output.py`](../hooks/scripts/core/hook_output.py) | 出力 alias 付与 / `emit_output()` / `EXIT_OK` / `EXIT_BLOCK` |
| [`hooks/scripts/tooling/tool_input.py`](../hooks/scripts/tooling/tool_input.py) | `is_write_tool()` / `is_read_tool()` / `get_written_paths()` / `get_read_paths()` |

---

## トリガーフレーズ

以下のようなフレーズを入力すると、このスキルが自動的に参照されます。

- 「フックを作成して」「hook script を書いて」
- 「PreToolUse / PostToolUse フックを実装したい」
- 「exit code 2 でブロックするには？」
- 「permissionDecision の使い方は？」
- 「hook のデバッグ方法を教えて」
- 「新しいフック設定ファイルを追加したい」

---

## Key ポイント（よくある間違い）

| 間違い | 正しい対応 |
| --- | --- |
| `continue: false` でツール単体をブロック | `permissionDecision: "deny"` または `sys.exit(2)` を使う |
| `stop_hook_active` を確認しない | `Stop`/`SubagentStop` では必ず確認して無限ループを防ぐ |
| `SubagentStop` で `hookSpecificOutput.decision` を使う | `SubagentStop` はトップレベルの `decision` を使う（`Stop` と異なる） |
| `timestamp` を整数（Unix ms）として扱う | VS Code では ISO 8601 文字列 |
| `permissionDecision: "ask"` が動かない | VS Code のみ対応（Cloud Agent/CLI では動作しない） |
| スクリプト内で `payload.get("tool_name")` を直接利用 | `hook_payload.py` を import し `get_hook_input()` または `get_hook_input_as()` で型付きオブジェクトを取得 |
| 読み取りアクセス制御に書き込みツール判定を流用 | `is_read_tool()` + `get_read_paths()` を使う（`tool_input.py`） |
