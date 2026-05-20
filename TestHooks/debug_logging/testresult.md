# testresult: debug_logging.py

対象スクリプト: `.github/hooks/scripts/shared/debug_logging.py`
実行日: 2026-05-05
コミットID: 32ed3c0
実行コマンド: `python -m unittest test_debug_logging -v`
総合結果: **PASS** (9/9)

---

## テスト結果

| テストID | 観点 | 入力 | 期待動作 | 結果 | 判定 |
|----------|------|------|----------|------|------|
| DL-001 | `build_debug_paths` フラグファイルパス名 | `script_dir, "foo"` | フラグファイルパスが `foo.debug` になる | `foo.debug` | PASS |
| DL-002 | `build_debug_paths` ログファイルパス名 | `script_dir, "foo"` | ログファイルパスが `foo.debug.log` になる | `foo.debug.log` | PASS |
| DL-003 | `is_debug_enabled` フラグファイル存在時 | フラグファイルを作成した状態 | `True` を返す | `True` | PASS |
| DL-004 | `is_debug_enabled` フラグファイル不在時 | フラグファイルが存在しない状態 | `False` を返す | `False` | PASS |
| DL-005 | `HookDebugLogger.log` デバッグ有効・kwargs 有り | フラグ有り, `message="input"`, `key="value"` | ログファイルに `"input"` と `"key"` を含む行が追記される | ログに `"input"` と `"key"` 含む | PASS |
| DL-006 | `HookDebugLogger.log` デバッグ有効・kwargs 無し | フラグ有り, `message="done"` | ログファイルに `"done"` のみの行が追記される | ログに `"done"` のみ | PASS |
| DL-007 | `HookDebugLogger.log` デバッグ無効 | フラグなし, `message="skip"` | ログファイルへの書き込みが発生しない | ログファイル未作成 | PASS |
| DL-008 | `append_debug_line` 新規ファイル作成 | 存在しないパス, `"first line"` | ファイルを新規作成して内容が書き込まれる | ファイル作成 + `"first line"` 含む | PASS |
| DL-009 | `append_debug_line` 既存ファイルへ追記 | 既存ファイル, `"second line"` | 既存の内容を保持し末尾に追記される | `"line1"` + `"line2"` 両方含む | PASS |
