# testcase: tool_input.py

対象スクリプト: `.github/hooks/scripts/tool_input.py`

---

## テストケース一覧

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| TI-001 | `is_write_tool` — create_file | `"create_file"` | `True` を返す |
| TI-002 | `is_write_tool` — replace_string_in_file | `"replace_string_in_file"` | `True` を返す |
| TI-003 | `is_write_tool` — multi_replace_string_in_file | `"multi_replace_string_in_file"` | `True` を返す |
| TI-004 | `is_write_tool` — 非 write ツール | `"read_file"` | `False` を返す |
| TI-005 | `is_read_tool` — read_file | `"read_file"` | `True` を返す |
| TI-006 | `is_read_tool` — list_dir | `"list_dir"` | `True` を返す |
| TI-007 | `is_read_tool` — view_image | `"view_image"` | `True` を返す |
| TI-008 | `is_read_tool` — 非 read ツール | `"create_file"` | `False` を返す |
| TI-009 | `get_written_paths` — create_file filePath 有り | `tool_name="create_file"`, `{"filePath": "a.py"}` | `["a.py"]` を返す |
| TI-010 | `get_written_paths` — create_file filePath 無し | `tool_name="create_file"`, `{}` | `[]` を返す |
| TI-011 | `get_written_paths` — multi_replace 配列 2 件 | `replacements` に 2 件の `filePath` 有り | 2 パスのリストを返す |
| TI-012 | `get_written_paths` — multi_replace empty + filePath fallback | `replacements=[]` + `filePath="x.md"` | `["x.md"]` を返す |
| TI-013 | `get_written_paths` — 非 write ツール | `tool_name="read_file"`, `{"filePath": "x.py"}` | `[]` を返す |
| TI-014 | `get_read_paths` — read_file | `tool_name="read_file"`, `{"filePath": "x.py"}` | `["x.py"]` を返す |
| TI-015 | `get_read_paths` — list_dir | `tool_name="list_dir"`, `{"path": "/tmp"}` | `["/tmp"]` を返す |
| TI-016 | `get_command` — command キー有り | `{"command": "ls -la"}` | `"ls -la"` を返す |
| TI-017 | `get_read_paths` — 非 read ツール | `tool_name="create_file"`, `{"filePath": "x.py"}` | `[]` を返す |
| TI-018 | `get_read_paths` — view_image | `tool_name="view_image"`, `{"filePath": "img.png"}` | `["img.png"]` を返す |
| TI-019 | `get_read_paths` — read_file filePath 無し | `tool_name="read_file"`, `{}` | `[]` を返す |
| TI-020 | `get_read_paths` — list_dir path 無し | `tool_name="list_dir"`, `{}` | `[]` を返す |
| TI-021 | `get_command` — command キー無し | `{}` | `""` を返す |
