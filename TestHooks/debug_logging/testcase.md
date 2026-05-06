# testcase: debug_logging.py

対象スクリプト: `.github/hooks/scripts/debug_logging.py`

---

## テストケース一覧

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| DL-001 | `build_debug_paths` フラグファイルパス名 | `script_dir, "foo"` | フラグファイルパスが `foo.debug` になる |
| DL-002 | `build_debug_paths` ログファイルパス名 | `script_dir, "foo"` | ログファイルパスが `foo.debug.log` になる |
| DL-003 | `is_debug_enabled` フラグファイル存在時 | フラグファイルを作成した状態 | `True` を返す |
| DL-004 | `is_debug_enabled` フラグファイル不在時 | フラグファイルが存在しない状態 | `False` を返す |
| DL-005 | `HookDebugLogger.log` デバッグ有効・kwargs 有り | フラグ有り, `message="input"`, `key="value"` | ログファイルに `"input"` と `"key"` を含む行が追記される |
| DL-006 | `HookDebugLogger.log` デバッグ有効・kwargs 無し | フラグ有り, `message="done"` | ログファイルに `"done"` のみの行が追記される |
| DL-007 | `HookDebugLogger.log` デバッグ無効 | フラグなし, `message="skip"` | ログファイルへの書き込みが発生しない |
| DL-008 | `append_debug_line` 新規ファイル作成 | 存在しないパス, `"first line"` | ファイルを新規作成して内容が書き込まれる |
| DL-009 | `append_debug_line` 既存ファイルへ追記 | 既存ファイル, `"second line"` | 既存の内容を保持し末尾に追記される |
