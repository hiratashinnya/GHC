# testresult: post_tool_dashboard_sync.py

対象スクリプト: `.github/hooks/scripts/entrypoints/post_tool_dashboard_sync.py`
実行日: 2026-05-05
コミットID: 32ed3c0
実行コマンド: `python -m unittest test_post_tool_dashboard_sync -v`
総合結果: **PASS** (11/11)

---

## テスト結果

| テストID | 観点 | 入力 | 期待動作 | 結果 | 判定 |
|----------|------|------|----------|------|------|
| DS-001 | `_should_skip` 非 write ツール | `tool_name="read_file"` | `reason="non-write tool"`, `changed_file=None` を返す | `("non-write tool", None)` | PASS |
| DS-002 | `_should_skip` docs 以外のファイル | `tool_name="create_file"`, `filePath="src/foo.py"` | `reason="not a docs/ .md file"` を返す | reason に `"docs"` 含む | PASS |
| DS-003 | `_should_skip` docs 配下 .md（相対パス） | `tool_name="create_file"`, `filePath="docs/x.md"` | `reason=None`, `changed_file="docs/x.md"` を返す | `(None, "docs/x.md")` | PASS |
| DS-004 | `_should_skip` docs 配下 .md（絶対パス） | workspace 絶対パス + `/docs/x.md` | `reason=None`, `changed_file="docs/x.md"`（POSIX 正規化済み）を返す | `(None, "docs/x.md")` | PASS |
| DS-005 | `_should_skip` docs 配下だが .md 以外 | `filePath="docs/x.txt"` | `reason="not a docs/ .md file"` を返す | reason が `None` でない | PASS |
| DS-006 | `_build_patch_cmd` changed_file 有り | `patch_script`, `"docs/x.md"` | `--changed-file docs/x.md` がコマンドリストに含まれる | `--changed-file docs/x.md` 含む | PASS |
| DS-007 | `_build_patch_cmd` changed_file 無し（None） | `patch_script`, `None` | `--changed-file` がコマンドリストに含まれない | `--changed-file` 不在 | PASS |
| DS-008 | `main()` 非 write ツール → スキップ（exit=0） | stdin に `tool_name="read_file"` のペイロード | exit=0 で終了し `subprocess.run` が呼ばれない | `subprocess.run` 未呼出 | PASS |
| DS-009 | `main()` docs 外ファイル → スキップ（exit=0） | stdin に `filePath="src/foo.py"` のペイロード | exit=0 で終了し `subprocess.run` が呼ばれない | `subprocess.run` 未呼出 | PASS |
| DS-010 | `main()` docs/.md ファイル → patch 実行 | stdin に `filePath="docs/x.md"` のペイロード、patch_script は存在 | `subprocess.run` が呼ばれ、`changed_file="docs/x.md"` が引数に含まれる | `subprocess.run` 呼出、`--changed-file docs/x.md` 含む | PASS |
| DS-011 | `_should_skip` multi_replace で docs/.md を含む | `tool_name="multi_replace_string_in_file"`, `replacements` の先頭パスが docs/.md | `reason=None`, `changed_file="docs/y.md"` を返す | `(None, "docs/y.md")` | PASS |
