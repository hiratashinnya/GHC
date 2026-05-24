# testresult: tool_input_spy.py

対象スクリプト: `.github/hooks/scripts/entrypoints/tool_input_spy.py`
実行日: 2026-05-21
コミットID: e4b618f
実行コマンド: `cd TestHooks/tool_input_spy && python -m unittest test_tool_input_spy -v`
総合結果: **FAIL** (5/7, errors=2)

備考: `main()` のテストでは `sys.argv` を `["tool_input_spy.py", "--event", "PostToolUse"]` にモックし、`argparse` の干渉を回避。

---

## テスト結果

| テストID | 観点 | 入力 | 期待動作 | 結果 | 判定 |
|----------|------|------|----------|------|------|
| SP-001 | `_sanitize` 短文字列（トランケートなし） | 100 文字の文字列 | 変更されずそのまま返す | 元の文字列と一致 | PASS |
| SP-002 | `_sanitize` 長文字列（トランケート） | 400 文字の文字列 | 先頭 300 文字 + `...[truncated 100 chars]` の文字列を返す | 先頭 300 文字 + truncate メッセージ | PASS |
| SP-003 | `_sanitize` dict（ネスト処理） | `{"key": 400文字}` | value がトランケートされた dict を返す | value に `[truncated` 含む | PASS |
| SP-004 | `_sanitize` list（要素処理） | `[400文字, 100文字]` | 長い要素のみトランケートされたリストを返す | 先頭 truncate、2番目は元の値 | PASS |
| SP-005 | `main` デバッグ有効時 | デバッグフラグ有り + stdin にペイロード | ログファイルに `"spy"` ラベルのエントリが書き込まれる | `AttributeError: module 'hook_payload' has no attribute 'sys'` | ERROR |
| SP-006 | `main` デバッグ無効時 | デバッグフラグなし + stdin にペイロード | ログファイルへの書き込みが発生しない | `AttributeError: module 'hook_payload' has no attribute 'sys'` | ERROR |
| SP-007 | `_sanitize` 非文字列 dict 値（int） | `{"count": 42}` | `{"count": 42}` をそのまま返す（変換なし） | `{"count": 42}` | PASS |
