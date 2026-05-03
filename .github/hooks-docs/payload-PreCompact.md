# PreCompact — ペイロードリファレンス

会話コンテキストが圧縮（コンパクト化）される直前に発火する。重要な状態の保存・エクスポートに使用する。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "trigger": "auto"
}
```

| フィールド | 型 | 値 | 説明 |
|---|---|---|---|
| `trigger` | `string` | `"auto"` | 圧縮のトリガー。会話がプロンプトバジェットを超えた場合に `"auto"` |

---

## 出力 JSON

共通出力フィールド（`continue`, `stopReason`, `systemMessage`）のみサポート。
`hookSpecificOutput` は使用不可（無視される）。

→ [共通出力フィールド](../Hooks-instructions.md#共通出力フィールド全イベント共通)

> **出力省略時の動作**: 圧縮は正常に実行される。

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""PreCompact hook: save important state before context compaction."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "pre_compact")

STATE_FILE = Path(".github/hooks/logs/pre_compact_state.jsonl")


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    trigger = payload.get("trigger", "")
    session_id = payload.get("sessionId", "")
    cwd = payload.get("cwd", "")

    DEBUG.log("input", trigger=trigger, session_id=session_id)

    # 圧縮直前の状態をログ記録
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "event": "PreCompact",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "sessionId": session_id,
        "cwd": cwd
    }
    with open(STATE_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    DEBUG.log("done", trigger=trigger)
    print(json.dumps({"continue": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
