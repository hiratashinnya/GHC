# Stop — ペイロードリファレンス

エージェントセッションが終了する直前に発火する。後処理・レポート生成・エージェントの継続指示に使用する。

> **注意**: カスタムエージェント配下では `Stop` フックは `SubagentStop` としても扱われる。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "stop_hook_active": false
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `stop_hook_active` | `boolean` | 前回の Stop フックによってエージェントが継続されている場合 `true` |

> ⚠️ **`stop_hook_active` が `true` のときは `decision:"block"` を返してはならない。** 無限ループを防ぐために必ずこのフィールドを確認すること。

---

## 出力 JSON

エージェントの停止を防ぐ（継続を指示する）場合に `hookSpecificOutput` を使用する。

```json
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "decision": "block",
    "reason": "テストスイートを実行してから終了してください"
  }
}
```

| フィールド | 型 / 値 | 説明 |
|---|---|---|
| `hookSpecificOutput.hookEventName` | `"Stop"` | イベント名（必須） |
| `hookSpecificOutput.decision` | `"block"` | エージェントの停止を防ぎ継続させる |
| `hookSpecificOutput.reason` | `string` | `decision:"block"` 時は必須。エージェントになぜ継続すべきかを伝える |

> **⚠️ Stop フックでエージェントをブロックすると追加ターンが消費される（プレミアムリクエスト）。** 毎回の実行で `stop_hook_active` を確認し、無限ループを必ず防止すること。

> **出力省略時の動作**: セッションは正常終了する。

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""Stop hook: run test suite before session ends (once)."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "stop_hook")


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    stop_hook_active = payload.get("stop_hook_active", False)

    DEBUG.log("input", stop_hook_active=stop_hook_active)

    # 前回の Stop フックで継続中なら二重ブロックしない（無限ループ防止）
    if stop_hook_active:
        print(json.dumps({"continue": True}, ensure_ascii=False))
        return

    # テスト実行
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=short", "-q"],
        capture_output=True, text=True
    )
    DEBUG.log("test", returncode=result.returncode)

    if result.returncode != 0:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "decision": "block",
                "reason": (
                    "テストが失敗しています。修正してから終了してください:\n"
                    + result.stdout[-500:]
                )
            }
        }
        print(json.dumps(output, ensure_ascii=False))
        return

    print(json.dumps({"continue": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
