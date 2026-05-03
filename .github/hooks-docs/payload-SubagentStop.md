# SubagentStop — ペイロードリファレンス

サブエージェントが完了したときに発火する。結果の集約・後処理・サブエージェントの継続指示に使用する。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "agent_id": "subagent-456",
  "agent_type": "Plan",
  "stop_hook_active": false
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `agent_id` | `string` | サブエージェントの一意識別子 |
| `agent_type` | `string` | エージェント名 |
| `stop_hook_active` | `boolean` | 前回の SubagentStop フックで継続中の場合 `true` |

> ⚠️ **`stop_hook_active` が `true` のときは `decision:"block"` を返してはならない。** 無限ループ防止のために必ず確認すること。

---

## 出力 JSON

`Stop` とは異なり、**トップレベルの `decision`/`reason` フィールド**を使用する（`hookSpecificOutput` なし）。

```json
{
  "decision": "block",
  "reason": "サブエージェントの結果を検証してから完了してください"
}
```

| フィールド | 値 | 説明 |
|---|---|---|
| `decision` | `"block"` | サブエージェントの停止を防ぐ |
| `reason` | `string` | `decision:"block"` 時は必須。サブエージェントへの継続理由 |

> **`Stop` との出力形式の違いに注意:**
>
> | イベント | ブロック出力形式 |
> |---|---|
> | `Stop` | `hookSpecificOutput.decision:"block"` + `hookSpecificOutput.reason` |
> | `SubagentStop` | トップレベル `decision:"block"` + トップレベル `reason` |

> **出力省略時の動作**: サブエージェントは正常完了する。

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""SubagentStop hook: aggregate subagent results and log."""
from __future__ import annotations
import json, sys
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "subagent_stop")

LOG_FILE = SCRIPT_DIR / "subagent.jsonl"


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    agent_type = payload.get("agent_type", "")
    agent_id = payload.get("agent_id", "")
    stop_hook_active = payload.get("stop_hook_active", False)
    timestamp = payload.get("timestamp", "")

    DEBUG.log("input", agent_type=agent_type, agent_id=agent_id,
              stop_hook_active=stop_hook_active)

    # 無限ループ防止
    if stop_hook_active:
        print(json.dumps({"continue": True}, ensure_ascii=False))
        return

    # サブエージェント完了ログ
    entry = {
        "event": "SubagentStop",
        "timestamp": timestamp,
        "agent_id": agent_id,
        "agent_type": agent_type
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    DEBUG.log("done", agent_type=agent_type)
    print(json.dumps({"continue": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
