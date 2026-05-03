# UserPromptSubmit — ペイロードリファレンス

ユーザーがプロンプトを送信したときに発火する。ツール呼び出しより前の段階。監査ログ・コンテキスト注入・プロンプト解析に使用する。

## 共通フィールド

→ [Hooks-instructions.md § 共通フィールド](../Hooks-instructions.md#共通フィールド全イベント共通)

---

## 入力 JSON（専用フィールド）

```json
{
  "prompt": "Fix the authentication bug in src/auth.py"
}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `prompt` | `string` | ユーザーが送信したプロンプトのテキスト全体 |

> ⚠️ **プロンプトには機密情報（APIキー・パスワード等）が含まれる可能性がある。** ログ記録時は必要に応じてマスキングを行うこと。

---

## 出力 JSON

共通出力フィールド（`continue`, `stopReason`, `systemMessage`）のみサポート。
`hookSpecificOutput` は使用不可（無視される）。

→ [共通出力フィールド](../Hooks-instructions.md#共通出力フィールド全イベント共通)

| 用途 | 出力例 |
|---|---|
| ブロック不要（ログのみ） | 省略または `{"continue": true}` |
| プロンプトを拒否 | `{"continue": false, "stopReason": "禁止ワードが含まれています"}` |
| 警告メッセージ表示 | `{"systemMessage": "本番環境への変更です。注意してください"}` |

> **出力省略時の動作**: 処理は続行される（`{"continue": true}` と同等）。

---

## 実装スクリプト例（完全版）

```python
#!/usr/bin/env python3
"""UserPromptSubmit hook: audit log for user prompts."""
from __future__ import annotations
import json, re, sys
from pathlib import Path
from debug_logging import HookDebugLogger

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "log_prompt")

LOG_FILE = SCRIPT_DIR / "prompts.jsonl"

# 機密情報のマスキングパターン
_REDACT_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"gho_[A-Za-z0-9]{20,}"), "[REDACTED_TOKEN]"),
    (re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]+"), "Bearer [REDACTED]"),
    (re.compile(r"--password[= ]\S+"), "--password=[REDACTED]"),
]


def redact(text: str) -> str:
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def main() -> None:
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    payload = json.loads(raw) if raw else {}
    prompt = payload.get("prompt", "")
    timestamp = payload.get("timestamp", "")
    session_id = payload.get("sessionId", "")

    DEBUG.log("input", prompt_len=len(prompt))

    # プロンプトをマスキングしてログ記録
    entry = {
        "event": "UserPromptSubmit",
        "timestamp": timestamp,
        "sessionId": session_id,
        "prompt": redact(prompt)
    }
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(json.dumps({"continue": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```
