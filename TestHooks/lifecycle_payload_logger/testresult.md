# testresult: lifecycle_payload_logger.py

対象スクリプト: `.github/hooks/scripts/entrypoints/lifecycle_payload_logger.py`
実行日: 2026-05-24
コミットID: 7b5c2aa
実行コマンド: `cd TestHooks/lifecycle_payload_logger && python -m unittest test_lifecycle_payload_logger -v`
総合結果: **PASS** (6/6)

---

## テスト結果

| テストID | 観点 | 入力 | 期待動作 | 結果 | 判定 |
|----------|------|------|----------|------|------|
| LC-001 | `main` デバッグ無効時 | デバッグフラグなし + stdin に SessionStart ペイロード | ログファイルへの書き込みが発生しない | ログファイル未生成 | PASS |
| LC-002 | `main` デバッグ有効 + 対象イベント | デバッグフラグ有り + stdin に SessionStart ペイロード | ログファイルに `"input_json"` ラベルのエントリが書き込まれる | `input_json` を含む行が記録された | PASS |
| LC-003 | `main` デバッグ有効 + 非対象イベント | デバッグフラグ有り + stdin に PreToolUse ペイロード | ログファイルに `"skip"` が書き込まれ `"input_json"` は書き込まれない | `skip` を含み `input_json` を含まない | PASS |
| LC-004 | タイムスタンプ形式 | デバッグフラグ有り + stdin に SubagentStart ペイロード | ログ行が `YYYY/MM/DD HH:MM:SS` 形式のタイムスタンプで始まる | 正規表現 `\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}` にマッチする行あり | PASS |
| LC-005 | 全ての対象イベントを処理 | SessionStart/Stop/SubagentStart/SubagentStop | 全て `"input_json"` が記録される | 全 4 イベントで `input_json` が記録された | PASS |
| LC-006 | ペイロードが二重 JSON シリアライズされない | デバッグフラグ有り + stdin に SessionStart ペイロード | `input_payload` が文字列でなく構造化 JSON として記録される | `\\"key\\"` 形式のエスケープなし、`key` が直接含まれる | PASS |
