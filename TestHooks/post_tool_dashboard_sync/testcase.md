# testcase: post_tool_dashboard_sync.py

対象スクリプト: `.github/hooks/scripts/post_tool_dashboard_sync.py`

---

## テストケース一覧

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| DS-001 | `_should_skip` 非 write ツール | `tool_name="read_file"` | `reason="non-write tool"`, `changed_file=None` を返す |
| DS-002 | `_should_skip` docs 以外のファイル | `tool_name="create_file"`, `filePath="src/foo.py"` | `reason="not a docs/ .md file"` を返す |
| DS-003 | `_should_skip` docs 配下 .md（相対パス） | `tool_name="create_file"`, `filePath="docs/x.md"` | `reason=None`, `changed_file="docs/x.md"` を返す |
| DS-004 | `_should_skip` docs 配下 .md（絶対パス） | workspace 絶対パス + `/docs/x.md` | `reason=None`, `changed_file="docs/x.md"`（POSIX 正規化済み）を返す |
| DS-005 | `_should_skip` docs 配下だが .md 以外 | `filePath="docs/x.txt"` | `reason="not a docs/ .md file"` を返す |
| DS-006 | `_build_patch_cmd` changed_file 有り | `patch_script`, `"docs/x.md"` | `--changed-file docs/x.md` がコマンドリストに含まれる |
| DS-007 | `_build_patch_cmd` changed_file 無し（None） | `patch_script`, `None` | `--changed-file` がコマンドリストに含まれない |
| DS-008 | `main()` 非 write ツール → スキップ（exit=0） | stdin に `tool_name="read_file"` のペイロード | exit=0 で終了し `subprocess.run` が呼ばれない |
| DS-009 | `main()` docs 外ファイル → スキップ（exit=0） | stdin に `filePath="src/foo.py"` のペイロード | exit=0 で終了し `subprocess.run` が呼ばれない |
| DS-010 | `main()` docs/.md ファイル → patch 実行 | stdin に `filePath="docs/x.md"` のペイロード、patch_script は存在 | `subprocess.run` が呼ばれ、`changed_file="docs/x.md"` が引数に含まれる |
| DS-011 | `_should_skip` multi_replace で docs/.md を含む | `tool_name="multi_replace_string_in_file"`, `replacements` の先頭パスが docs/.md | `reason=None`, `changed_file="docs/y.md"` を返す |
