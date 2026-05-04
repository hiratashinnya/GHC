# ツール別 tool_input スキーマ

VS Code GitHub Copilot hooks の `PreToolUse` / `PostToolUse` イベントで受け取る `tool_input` オブジェクトのフィールド仕様。

> `(省略可)` = パラメータが省略された場合はキー自体がペイロードに含まれないことがある。

---

## ファイル読み取り系

| ツール | キー | 型 | 説明 |
|---|---|---|---|
| `read_file` | `filePath` | `string` | 絶対パス |
| | `startLine` | `integer` | 読み取り開始行（1-based） |
| | `endLine` | `integer` | 読み取り終了行（1-based, inclusive） |
| `list_dir` | `path` | `string` | 絶対パス |
| `view_image` | `filePath` | `string` | 絶対パス |

---

## ファイル書き込み系 ⚠️

> これらのツールのみ「書き込みツール」として扱うこと（`read_file` 等も `filePath` を持つため混同注意）。

| ツール | キー | 型 | 説明 |
|---|---|---|---|
| `replace_string_in_file` | `filePath` | `string` | 絶対パス |
| | `oldString` | `string` | 置換前文字列 |
| | `newString` | `string` | 置換後文字列 |
| `create_file` | `filePath` | `string` | 絶対パス |
| | `content` | `string` | ファイル内容 |
| `multi_replace_string_in_file` | `filePath` | `string` | 対象ファイルパス（トップレベル） |
| | `replacements` | `array` | 各要素に `filePath`, `oldString`, `newString` |
| | `explanation` | `string` | 変更の説明（省略可） |

> `multi_replace_string_in_file` のトップレベル `filePath` は **単一ファイル編集時のみ**有効。
> 複数ファイルにまたがる場合は `replacements[].filePath` を参照すること。

---

## 検索・探索系

| ツール | キー | 型 | 説明 |
|---|---|---|---|
| `grep_search` | `query` | `string` | 検索パターン |
| | `isRegexp` | `boolean` | 正規表現フラグ |
| | `includePattern` | `string` | ファイルパスフィルタ（省略可） |
| | `maxResults` | `integer` | 最大件数（省略可） |
| | `includeIgnoredFiles` | `boolean` | .gitignore 無視（省略可） |
| `file_search` | `query` | `string` | glob パターン |
| | `maxResults` | `integer` | 最大件数（省略可） |
| `semantic_search` | `query` | `string` | 自然言語クエリ |

---

## ターミナル・実行系

| ツール | キー | 型 | 説明 |
|---|---|---|---|
| `run_in_terminal` | `command` | `string` | 実行コマンド |
| | `explanation` | `string` | コマンドの説明文 |
| | `goal` | `string` | 目的 |
| | `mode` | `string` | `"sync"` or `"async"` |
| | `timeout` | `integer` | タイムアウト（ms, 省略可） |
| `get_terminal_output` | `id` | `string` | ターミナルセッション ID |
| `get_errors` | `filePaths` | `array[string]` | チェック対象ファイルパス一覧 |

---

## エージェント・ツール連携系

| ツール | キー | 型 | 説明 |
|---|---|---|---|
| `runSubagent` | `prompt` | `string` | サブエージェントへの指示 |
| | `description` | `string` | タスク概要 |
| | `agentName` | `string` | エージェント名（省略可） |
| `tool_search` | `query` | `string` | ツール検索クエリ |
| `vscode_askQuestions` | `questions` | `array` | 質問リスト |

---

## メモリ・状態管理系

| ツール | キー | 型 | 説明 |
|---|---|---|---|
| `memory` | `command` | `string` | `create` / `view` / `str_replace` / `insert` / `delete` / `rename` |
| | `path` | `string` | メモリファイルパス |
| | `file_text` | `string` | `create` 時のファイル内容（省略可） |
| | `old_str` | `string` | `str_replace` 時の検索文字列（省略可） |
| | `new_str` | `string` | `str_replace` 時の置換文字列（省略可） |
| `manage_todo_list` | `todoList` | `array` | TODO 項目リスト |

---

## ツール分類表

フックスクリプトでファイル変更を検知する場合は、**書き込みツールのみ**を対象とすること。

| 分類 | ツール名 |
|---|---|
| **書き込み** | `replace_string_in_file`, `create_file`, `multi_replace_string_in_file` |
| **読み取り** | `read_file`, `list_dir`, `view_image` |
| **検索** | `grep_search`, `file_search`, `semantic_search` |
| **実行** | `run_in_terminal`, `get_terminal_output`, `get_errors` |
| **状態管理** | `memory`, `manage_todo_list` |
| **エージェント** | `runSubagent`, `tool_search`, `vscode_askQuestions` |

> `read_file` も `filePath` キーを持つため、ツール名フィルタなしに `tool_input.filePath` を「書き込みパス」として使うと誤検知する。

---

## 書き込みツールのファイルパス取得パターン（Python）

> **ライブラリ化済み**: `tool_input.py` の `get_written_paths()` を使用すること。
> 以下は参照用の実装例。

```python
def _extract_written_paths(tool_name: str, tool_input: dict) -> list[str]:
    """書き込みツールから変更対象ファイルパスを抽出する。"""
    if tool_name == "multi_replace_string_in_file":
        # 複数ファイルの場合は replacements から取得
        replacements = tool_input.get("replacements") or []
        paths = [r.get("filePath", "") for r in replacements if r.get("filePath")]
        if not paths:
            # 単一ファイルの場合はトップレベルの filePath
            fp = tool_input.get("filePath", "")
            if fp:
                paths = [fp]
        return paths
    elif tool_name in ("replace_string_in_file", "create_file"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []
    return []
```

---

## 読み取りツールのファイルパス取得パターン（Python）

> **ライブラリ化済み**: `tool_input.py` の `get_read_paths()` を使用すること。

```python
def _extract_read_paths(tool_name: str, tool_input: dict) -> list[str]:
    """読み取りツールからアクセス対象パスを抽出する。"""
    if tool_name in ("read_file", "view_image"):
        fp = tool_input.get("filePath", "")
        return [fp] if fp else []
    if tool_name == "list_dir":
        p = tool_input.get("path", "")
        return [p] if p else []
    return []
```

> **注意**: `read_file` と `view_image` はともに `filePath` キーを使用する。`list_dir` は `path` キーを使用する点に注意。

---

## ライブラリ参照

フックスクリプトからは直接 `tool_input.py` をインポートして使用すること:

```python
from tool_input import (
    is_write_tool, get_written_paths,   # 書き込みアクセス制御
    is_read_tool,  get_read_paths,      # 読み取りアクセス制御
    get_command,                         # run_in_terminal コマンド取得
)
```
