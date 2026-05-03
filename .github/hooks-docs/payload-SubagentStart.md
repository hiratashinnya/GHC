# SubagentStart — ペイロードリファレンス

サブエージェントが起動されたときに発火する。ネストされたエージェントのトラッキング・初期コンテキスト注入に使用する。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "agent_id": "subagent-456",
  "agent_type": "Plan"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `agent_id` | `string` | サブエージェントの一意識別子 |
| `agent_type` | `string` | エージェント名（例: `"Plan"` などのビルトイン名、またはカスタムエージェント名） |

---

## 出力 JSON

サブエージェントの会話に追加コンテキストを注入できる。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SubagentStart",
    "additionalContext": "このサブエージェントはプロジェクトのコーディング規約に従うこと"
  }
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `hookSpecificOutput.hookEventName` | `string` | `"SubagentStart"` 固定（必須） |
| `hookSpecificOutput.additionalContext` | `string` | サブエージェントの会話に注入するコンテキスト |

> **出力省略時の動作**: 処理は続行される。

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""SubagentStart hook: inject project guidelines into subagent context."""
from __future__ import annotations
import json, sys
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "subagent_start")

GUIDELINES_FILE = Path("docs/GUIDELINES.md")


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    agent_type = payload.get("agent_type", "")
    agent_id = payload.get("agent_id", "")

    DEBUG.log("input", agent_type=agent_type, agent_id=agent_id)

    context_parts = [f"Subagent type: {agent_type}"]
    if GUIDELINES_FILE.exists():
        # ガイドラインの先頭 1000 文字を注入（長すぎる場合は要約を推奨）
        context_parts.append(
            "--- Project Guidelines ---\n"
            + GUIDELINES_FILE.read_text(encoding="utf-8")[:1000]
        )

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": "\n".join(context_parts)
        }
    }
    DEBUG.log("done", agent_type=agent_type)
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
