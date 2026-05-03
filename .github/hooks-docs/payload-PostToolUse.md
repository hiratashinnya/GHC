# PostToolUse — ペイロードリファレンス

ツールの実行が完了した後に発火する（成功・失敗を問わない）。後処理・監査ログ・追加コンテキスト注入に使用する。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "tool_name": "replace_string_in_file",
  "tool_input": { "filePath": "docs/design.md", "oldString": "...", "newString": "..." },
  "tool_use_id": "tool-abc123",
  "tool_response": "File edited successfully"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `tool_name` | `string` | 実行されたツール名 |
| `tool_input` | `object` | ツール引数（→ [tool-input-schema.md](tool-input-schema.md) 参照） |
| `tool_use_id` | `string` | この呼び出しの一意識別子 |
| `tool_response` | `any` | ツールの実行結果。`str` または `dict` のいずれかになる場合がある |

> **注意**: `tool_response` の型はツールごとに異なる。スクリプト内では `str` / `dict` 両方に対応すること。

---

## 出力 JSON

後続処理のブロックまたはコンテキスト追加が可能。省略時は処理が続行される。

```json
{
  "decision": "block",
  "reason": "Lint errors detected in the edited file",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "編集後ファイルに lint エラーがあります。修正してください。"
  }
}
```

| フィールド | 値 | 説明 |
|---|---|---|
| `decision` | `"block"` | 後続処理を停止（省略可） |
| `reason` | `string` | ブロック理由（モデルに表示）。`decision:"block"` 時に使用 |
| `hookSpecificOutput.hookEventName` | `"PostToolUse"` | イベント名（必須） |
| `hookSpecificOutput.additionalContext` | `string` | 会話に注入する追加コンテキスト（省略可） |

> **出力省略時の動作**: 何も返さない（または `{"continue": true}` のみ）でも問題なし。ダッシュボード更新のような副作用だけを行うフックでは出力不要。

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""PostToolUse hook: update dashboard after docs/*.md writes."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "post_tool_example")

WRITE_TOOLS = {"replace_string_in_file", "create_file", "multi_replace_string_in_file"}


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    DEBUG.log("input", tool_name=tool_name)

    # 書き込みツール以外はスキップ
    if tool_name not in WRITE_TOOLS:
        print(json.dumps({"continue": True}, ensure_ascii=False))
        return

    file_path = tool_input.get("filePath", "")
    if not file_path.replace("\\", "/").startswith("docs/"):
        print(json.dumps({"continue": True}, ensure_ascii=False))
        return

    # ダッシュボード更新処理
    result = subprocess.run(
        ["python", ".github/scripts/patch_dashboard.py", "--changed-file", file_path],
        capture_output=True, text=True
    )
    DEBUG.log("done", returncode=result.returncode)

    if result.returncode != 0:
        DEBUG.log("error", stderr=result.stderr[:500])

    print(json.dumps({"continue": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
