# GitHub Copilot Hooks — 実装ガイド

> ステータス: 調査完了 (2026-04-27) / 照合更新 (2026-05-03)
> 調査ツール: `tool_input_spy` フック（PreToolUse / PostToolUse）
> データソース: `post_tool_dashboard_sync.debug.log`

> **重要 — 対象スコープ:**  
> このドキュメントは **VS Code GitHub Copilot Chat エージェント hooks** のスキーマを実測データに基づいて記述する。  
> GitHub.com の **Copilot Cloud Agent / GitHub Copilot CLI** の公式フック仕様（`toolName`, `toolArgs`, `permissionDecision` 等）とは **スキーマが異なる別システム** である。  
> 公式リファレンス（Cloud Agent/CLI 向け）: https://docs.github.com/en/copilot/reference/hooks-configuration

---

## 1. Hook ペイロード構造

### 共通フィールド（全イベント共通）

| フィールド | 型 | 説明 |
|---|---|---|
| `timestamp` | `string` | ISO 8601 形式のタイムスタンプ（例: `"2026-02-09T10:30:00.000Z"`） |
| `cwd` | `string` | 実行時のワーキングディレクトリ（絶対パス） |
| `sessionId` | `string` | セッション識別子 |
| `hookEventName` | `string` | フックイベント名（例: `"PreToolUse"`） |
| `transcript_path` | `string` | トランスクリプトファイルのパス |

> **注意**: `timestamp` は ISO 8601 文字列。Cloud Agent/CLI の Unix ミリ秒形式とは異なる。

### 全8イベント一覧

各イベントの詳細なペイロード仕様（入出力 JSON・フィールド一覧・実装例）は各リンク先を参照。

| イベント | 発火タイミング | 入力固有フィールド | 出力タイプ | 詳細 |
|---|---|---|---|---|
| `PreToolUse` | ツール実行直前 | `tool_name`, `tool_input`, `tool_use_id` | `hookSpecificOutput.permissionDecision` / exit 2 | [payload-PreToolUse.md](hooks-docs/payload-PreToolUse.md) |
| `PostToolUse` | ツール実行直後 | `tool_name`, `tool_input`, `tool_use_id`, `tool_response` | `decision:"block"`, `hookSpecificOutput.additionalContext` | [payload-PostToolUse.md](hooks-docs/payload-PostToolUse.md) |
| `UserPromptSubmit` | ユーザープロンプト送信時 | `prompt` | common のみ | [payload-UserPromptSubmit.md](hooks-docs/payload-UserPromptSubmit.md) |
| `SessionStart` | セッション開始時 | `source` | `hookSpecificOutput.additionalContext` | [payload-SessionStart.md](hooks-docs/payload-SessionStart.md) |
| `Stop` | セッション終了時 | `stop_hook_active` | `hookSpecificOutput.decision:"block"` | [payload-Stop.md](hooks-docs/payload-Stop.md) |
| `SubagentStart` | サブエージェント起動時 | `agent_id`, `agent_type` | `hookSpecificOutput.additionalContext` | [payload-SubagentStart.md](hooks-docs/payload-SubagentStart.md) |
| `SubagentStop` | サブエージェント完了時 | `agent_id`, `agent_type`, `stop_hook_active` | top-level `decision:"block"` | [payload-SubagentStop.md](hooks-docs/payload-SubagentStop.md) |
| `PreCompact` | コンテキスト圧縮直前 | `trigger` | common のみ | [payload-PreCompact.md](hooks-docs/payload-PreCompact.md) |

### 共通出力フィールド（全イベント共通）

```json
{
  "continue": false,
  "stopReason": "Security policy violation",
  "systemMessage": "警告メッセージ"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `continue` | `boolean` | `false` で**セッション全体を停止**（デフォルト: `true`） |
| `stopReason` | `string` | 停止理由（ユーザーに表示）。`continue: false` 時に使用 |
| `systemMessage` | `string` | ユーザーへの警告メッセージ（チャットに表示） |

> ⚠️ `continue: false` は**ツール1回のブロックではなく、セッション全体の停止**。単一ツール呼び出しのブロックには `hookSpecificOutput.permissionDecision: "deny"` または exit code 2 を使用すること。

---

## 2. ツール別 tool_input スキーマ

詳細は [hooks-docs/tool-input-schema.md](hooks-docs/tool-input-schema.md) を参照。

---

## 3. PreToolUse vs PostToolUse

| 観点 | PreToolUse | PostToolUse |
|---|---|---|
| 発火タイミング | ツール実行直前 | ツール実行直後 |
| `tool_response` の有無 | なし | あり |
| ツール単体のブロック | `hookSpecificOutput.permissionDecision: "deny"` または **exit code 2** | `decision: "block"` |
| セッション全体の停止 | `{"continue": false}` + `stopReason` | `{"continue": false}` + `stopReason` |
| 続行 | exit code 0（`{"continue": true}` を明示出力するのがベストプラクティス） | n/a |
| ユーザー承認 | `permissionDecision: "ask"` で**実装済み** | 非対応 |
| 用途例 | ゲートチェック、権限確認 | ダッシュボード更新、後処理 |

> **exit code のセマンティクス（公式ドキュメント）:**
>
> | exit code | 動作 |
> |---|---|
> | `0` | 成功: stdout を JSON として解析 |
> | `2` | ブロックエラー: 処理を停止しエラーをモデルに表示 |
> | その他の非ゼロ | 非ブロック警告: 警告をユーザーに表示し処理は続行 |
>
> ⚠️ **exit code 1（やその他非ゼロ）は警告扱いで処理が続行される。** ブロックには必ず **exit code 2** を使用すること。

> **注意 — ブロックの実装方針:**  
> `check_phase_gate.py` は `sys.exit(2)` でブロックする（正しい実装）。  
> `continue: false` はツール1回ではなく**セッション全体を停止**する別の仕組みであり、フェーズゲートには不適切。

> **注意 — ユーザー承認:**  
> VS Code の `permissionDecision: "ask"` は**実装済み**（Cloud Agent/CLI とは異なる）。  
> `"ask"` を返すと VS Code がユーザーに確認ダイアログを表示する。  
> Cloud Agent/CLI の公式ドキュメントでは `"deny"` のみが現在処理されると明記されており、**プラットフォームによって実装状況が異なる**。

---

## 4. 書き込みツール vs 読み取りツール — 分類表

詳細は [hooks-docs/tool-input-schema.md](hooks-docs/tool-input-schema.md) の「ツール分類表」セクションを参照。

---

## 5. スパイフックの使い方

`tool_input_spy` フックは全ツールの入出力を `tool_input_spy.debug.log` に記録する調査専用フックです。

### 有効化

```powershell
New-Item .\.github\hooks\scripts\tool_input_spy.debug -ItemType File -Force
```

### 無効化

```powershell
Remove-Item .\.github\hooks\scripts\tool_input_spy.debug
```

### ログ確認

```powershell
Get-Content .\.github\hooks\scripts\tool_input_spy.debug.log | Select-Object -Last 30
```

### ログ形式（例）

```
spy | {"event": "PostToolUse", "tool_name": "replace_string_in_file", "tool_input": {"filePath": "docs/foo.md", "oldString": "...", "newString": "..."}}
spy | {"event": "PreToolUse",  "tool_name": "read_file",              "tool_input": {"filePath": "docs/foo.md", "startLine": 1, "endLine": 50}}
```

> デフォルトでは OFF（`.debug` ファイルなし）。スキーマ調査時のみ有効化し、完了後は無効化すること。

---

## 6. 新規フック作成チェックリスト

チェックリスト・Python テンプレートについては [hooks-docs/hook-template.md](hooks-docs/hook-template.md) を参照。

---

## 7. 既存フック一覧

| ファイル | イベント | スクリプト | 役割 |
|---|---|---|---|
| `hooks/dashboard-sync.json` | PostToolUse | `post_tool_dashboard_sync.py` | docs/*.md 書き込み後にダッシュボードを同期 |
| `hooks/phase-gate.json` | PreToolUse | `check_phase_gate.py` | フェーズゲートチェック（承認確認） |
| `hooks/lifecycle-payload-log.json` | SessionStart / Stop / SubagentStart / SubagentStop | `lifecycle_payload_logger.py` | セッション/サブエージェントの開始・終了イベント入力 JSON をデバッグログ出力 |
| `hooks/tool-spy.json` | PreToolUse / PostToolUse | `tool_input_spy.py` | 全ツールの tool_input を調査ログに記録（調査専用） |
