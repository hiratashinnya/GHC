# testresult: workspace_utils.py

対象スクリプト: `.github/hooks/scripts/workspace_utils.py`
実行日: 2026-05-08
コミットID: d8db764 (未コミット変更あり: _lib 一元管理統合)
実行コマンド: `python -m unittest TestHooks/workspace_utils/test_workspace_utils.py -v`
総合結果: **PASS** (16/16)

---

## テスト結果

| テストID | 観点 | 入力 | 期待動作 | 結果 | 判定 |
|----------|------|------|----------|------|------|
| WU-001 | `norm` バックスラッシュ変換 | `"docs\\basic-design\\x.md"` | `"docs/basic-design/x.md"` を返す | `"docs/basic-design/x.md"` | PASS |
| WU-002 | `norm` POSIX済みパス（変換不要） | `"docs/basic-design/x.md"` | そのまま `"docs/basic-design/x.md"` を返す | `"docs/basic-design/x.md"` | PASS |
| WU-003 | `norm` 空文字 | `""` | `""` を返す | `""` | PASS |
| WU-004 | `to_workspace_relative` ワークスペース内の絶対パス | workspace 配下の絶対パス | ワークスペース相対 POSIX 文字列を返す | `"docs/x.md"` | PASS |
| WU-005 | `to_workspace_relative` ワークスペース相対パス | `"docs/x.md"` + workspace_path | `"docs/x.md"` を返す | `"docs/x.md"` | PASS |
| WU-006 | `to_workspace_relative` ワークスペース外のパス | workspace 外の絶対パス | `None` を返す | `None` | PASS |
| WU-007 | `to_workspace_relative` ワークスペース直下ファイル | workspace ルート直下の絶対パス | `"README.md"` を返す（先頭スラッシュなし） | `"README.md"` | PASS |
| WU-008 | `is_under_dir` 配下にあるファイル | `"docs/x.md"`, subdir=`"docs"` | `True` を返す | `True` | PASS |
| WU-009 | `is_under_dir` subdir と完全一致 | `"docs"`, subdir=`"docs"` | `True` を返す | `True` | PASS |
| WU-010 | `is_under_dir` 兄弟ディレクトリのファイル | `"iter/x.md"`, subdir=`"docs"` | `False` を返す | `False` | PASS |
| WU-011 | `is_under_dir` ワークスペース外パス | workspace 外の絶対パス, subdir=`"docs"` | `False` を返す | `False` | PASS |
| WU-012 | `dedup_paths` 重複なし | `["a.md", "b.md"]` | `["a.md", "b.md"]` を返す（不変） | `["a.md", "b.md"]` | PASS |
| WU-013 | `dedup_paths` 完全重複 | `["a.md", "a.md"]` | `["a.md"]` を返す | `["a.md"]` | PASS |
| WU-014 | `dedup_paths` スラッシュ不一致による重複 | `["docs\\x.md", "docs/x.md"]` | `["docs/x.md"]` を返す（1件に集約） | `["docs/x.md"]` | PASS |
| WU-015 | `dedup_paths` 空リスト | `[]` | `[]` を返す | `[]` | PASS |
| WU-016 | `dedup_paths` 挿入順を保持 | `["b.md", "a.md", "b.md"]` | `["b.md", "a.md"]` を返す | `["b.md", "a.md"]` | PASS |
