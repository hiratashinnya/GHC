# testcase: lifecycle_payload_logger.py

対象スクリプト: `.github/hooks/scripts/entrypoints/lifecycle_payload_logger.py`

---

## テストケース一覧

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| LC-001 | `main` デバッグ無効時 | デバッグフラグなし + stdin に SessionStart ペイロード | ログファイルへの書き込みが発生しない |
| LC-002 | `main` デバッグ有効 + 対象イベント | デバッグフラグ有り + stdin に SessionStart ペイロード | ログファイルに `"input_json"` ラベルのエントリが書き込まれる |
| LC-003 | `main` デバッグ有効 + 非対象イベント | デバッグフラグ有り + stdin に PreToolUse ペイロード | ログファイルに `"skip"` ラベルのエントリが書き込まれ、`"input_json"` は書き込まれない |
| LC-004 | タイムスタンプ形式 | デバッグフラグ有り + stdin に SubagentStart ペイロード | ログ行が `YYYY/MM/DD HH:MM:SS` 形式のタイムスタンプで始まる |
| LC-005 | 全ての対象イベントを処理 | 各対象イベント名 (SessionStart/Stop/SubagentStart/SubagentStop) | 全て `"input_json"` が記録される |
| LC-006 | ペイロードが二重 JSON シリアライズされない | デバッグフラグ有り + stdin に SessionStart ペイロード | ログ内の `input_payload` が文字列でなく構造化 JSON として記録される（エスケープ済み文字列ではない） |
