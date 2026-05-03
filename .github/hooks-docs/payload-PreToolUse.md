# PreToolUse — ペイロードリファレンス

エージェントがツールを呼び出す直前に実行される。ツール実行のブロック・承認・変更ができる最も強力なフックイベント。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "tool_name": "replace_string_in_file",
  "tool_input": { "filePath": "src/main.py", "oldString": "...", "newString": "..." },
  "tool_use_id": "tool-abc123"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `tool_name` | `string` | 実行されるツール名（例: `read_file`, `run_in_terminal`） |
| `tool_input` | `object` | ツール引数（→ [tool-input-schema.md](tool-input-schema.md) 参照） |
| `tool_use_id` | `string` | この呼び出しの一意識別子 |

---

## 出力 JSON

`hookSpecificOutput` ラッパーに包んで返す（省略可）。省略時はツール実行が許可される。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive command blocked by policy",
    "updatedInput": {},
    "additionalContext": "モデルへの追加コンテキスト"
  }
}
```

| フィールド | 値 | 説明 |
|---|---|---|
| `permissionDecision` | `"allow"` / `"deny"` / `"ask"` | ツール実行の承認制御（省略時は許可） |
| `permissionDecisionReason` | `string` | 判断理由（ユーザーに表示）。`deny`/`ask` 時に推奨 |
| `updatedInput` | `object` | 変更後のツール入力（省略可）。スキーマ不一致時は無視される |
| `additionalContext` | `string` | 会話に注入する追加コンテキスト（省略可） |

### permissionDecision 優先順位（複数フック競合時）

`deny` > `ask` > `allow`

> **`"ask"` は VS Code で実装済み** — ユーザーに確認ダイアログを表示して承認を求める。
> Cloud Agent/CLI では `"deny"` のみ現在処理される（プラットフォームにより実装状況が異なる）。

---

## ブロック実装パターン

### パターン 1: exit code 2（最もシンプル）

```python
# stderr の内容がモデルへのコンテキストとして渡される
print("危険なコマンドをブロックしました", file=sys.stderr)
sys.exit(2)
```

### パターン 2: permissionDecision deny

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "本番ファイルへの直接書き込みは禁止されています"
    }
}
print(json.dumps(output, ensure_ascii=False))
sys.exit(0)  # exit(2) と組み合わせも可
```

### パターン 3: ユーザー承認を求める（ask）

```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": "本番環境に影響する操作です。実行しますか？"
    }
}
print(json.dumps(output, ensure_ascii=False))
sys.exit(0)
```

### パターン 4: ツール入力を変更（updatedInput）

```python
# ファイルパスを安全なパスにリダイレクト
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "updatedInput": {
            "filePath": safe_path,
            "oldString": old_string,
            "newString": new_string
        }
    }
}
print(json.dumps(output, ensure_ascii=False))
```

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""PreToolUse hook: block dangerous terminal commands."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "my_pre_hook")

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"\bsudo\b",
    r"\bdrop\s+table\b",
    r"curl.*\|\s*(bash|sh)",
]


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}

    DEBUG.log("input", tool_name=tool_name, keys=list(tool_input.keys()))

    if tool_name == "run_in_terminal":
        command = tool_input.get("command", "")
        for pat in DANGEROUS_PATTERNS:
            if re.search(pat, command, re.IGNORECASE):
                reason = f"危険なコマンドをブロックしました（パターン: {pat}）"
                DEBUG.log("deny", reason=reason, command=command[:200])
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": reason
                    }
                }, ensure_ascii=False))
                sys.exit(2)

    DEBUG.log("allow", tool_name=tool_name)
    print(json.dumps({"continue": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
