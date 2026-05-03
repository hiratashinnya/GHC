# SessionStart — ペイロードリファレンス

新しいエージェントセッションが開始されたときに発火する。環境初期化・セッションログ・コンテキスト注入に使用する。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "source": "new"
}
```

| フィールド | 型 | 値 | 説明 |
|---|---|---|---|
| `source` | `string` | `"new"` | セッション開始方法。現在は常に `"new"` |

---

## 出力 JSON

`hookSpecificOutput` でエージェントの会話に追加コンテキストを注入できる。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Project: my-app v2.1.0 | Branch: main | Node: v20.11.0"
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `hookSpecificOutput.hookEventName` | `string` | `"SessionStart"` 固定（必須） |
| `hookSpecificOutput.additionalContext` | `string` | エージェントの会話に注入するコンテキスト文字列 |

> **出力省略時の動作**: 処理は続行される。

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""SessionStart hook: inject project context into agent conversation."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "session_start")


def _get_git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _get_git_status_summary() -> str:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().splitlines()
        return f"{len(lines)} uncommitted changes" if lines else "clean"
    except Exception:
        return "unknown"


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    source = payload.get("source", "")
    session_id = payload.get("sessionId", "")

    DEBUG.log("input", source=source, session_id=session_id)

    branch = _get_git_branch()
    git_status = _get_git_status_summary()
    context = f"Git branch: {branch} | Status: {git_status} | Hook policy: active"

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }
    DEBUG.log("done", branch=branch)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
