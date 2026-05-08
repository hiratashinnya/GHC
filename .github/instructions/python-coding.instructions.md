---
description: "Use when writing, editing, or reviewing Python scripts in this workspace. Enforces standard-library-only, dataclass-based type-safe design, unittest, thin main(), single-responsibility, and project-specific doc-style. Trigger phrases: python script, write python, hook script, lib module, python coding style, python implementation"
applyTo: "**/*.py"
---

# Python コーディング規約

## 依存関係

- **標準ライブラリのみ使用する。**`pip install` は禁止。
- 必要なサードパーティ機能は標準ライブラリで代替するか、プロジェクト内の `_lib/` モジュールを使う。

```python
# OK
import os, sys, json, re, subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List

# NG — 外部パッケージ禁止
import requests
import pydantic
```

## データ構造：dataclass を使う

`dict` や `tuple` の多用は禁止。複数フィールドを持つデータは必ず `@dataclass` で定義する。

```python
# NG
def process(data: dict) -> tuple:
    return (data["name"], data["value"])

# OK
from dataclasses import dataclass

@dataclass
class ProcessResult:
    name: str
    value: int
```

`field(default_factory=...)` を使い、KeyError を起こさない安全なデフォルトを設定する。

```python
@dataclass
class HookPayload:
    tool_name: str = ""
    tool_input: dict = field(default_factory=dict)
```

## 命名規則

命名は自己説明的であること。略語・単文字変数は禁止（ループカウンタ `i` は例外）。

| 対象 | スタイル | 例 |
|------|---------|-----|
| モジュール | `snake_case` | `hook_payload.py` |
| クラス | `PascalCase` | `PreToolUsePayload` |
| 関数・変数 | `snake_case` | `read_payload()`, `script_dir` |
| 定数 | `UPPER_SNAKE_CASE` | `EXIT_BLOCK = 2` |
| プライベート | 先頭 `_` | `_parse_frontmatter()` |

## 自己検証：実行時 assert / 事後条件

境界値・型・不変条件は `assert` または早期 `raise` で明示する。サイレントに壊れたデータを返さない。

```python
def phase_index(phase: str) -> int:
    if phase not in PHASE_INDEX:
        raise ValueError(f"Unknown phase: {phase!r}")
    return PHASE_INDEX[phase]
```

## main() の設計：薄く、1画面で意図が分かるように

`main()` は **オーケストレーション専用**。ロジックを直書きしない。
1画面（約30行以内）で「何をするスクリプトか」が読み取れるようにする。

```python
def main() -> None:
    payload, workspace, patch_script = _parse_input()
    changed_files = _extract_changed_docs(payload)
    if not changed_files:
        sys.exit(0)
    _run_patch(patch_script, workspace, changed_files)


if __name__ == "__main__":
    main()
```

- 入力取得 → 判定 → 処理 → 出力 の流れを明示する
- 早期 `sys.exit(0)` で不要な処理を避ける
- ヘルパー関数名は動詞+目的語形式（`_parse_input`, `_run_patch`）

## 単一責務の原則

1ファイル = 1責務。複数の関心を持ち込まない。

| ファイル例 | 責務 |
|-----------|------|
| `hook_payload.py` | ペイロードの読み込み・パースのみ |
| `debug_logging.py` | デバッグログの書き出しのみ |
| `tool_input.py` | ツール入力のパースのみ |
| `post_tool_dashboard_sync.py` | PostToolUse イベントのオーケストレーション |

関数も同様。1関数 = 1つのことだけ行う。

## モジュール・関数ドキュメント

モジュール先頭と各関数に以下の形式で docstring を書く。

```python
#!/usr/bin/env python3
"""モジュールの一言説明。

責務:
    このモジュールが担う唯一の仕事を記述する。

入力:
    関数引数の概要、または stdin / ファイル。

出力:
    戻り値の概要、または stdout / ファイル。

副作用:
    ファイル書き込み・プロセス起動など。なければ「なし」。

依存モジュール:
    使用する標準ライブラリ・内部モジュール名。
"""
```

関数レベルも同じ4項目（責務・入力・出力・副作用）を簡潔に記述する。

## テスト：unittest

テストは `unittest.TestCase` を使う。`pytest` は使わない。

```python
#!/usr/bin/env python3
"""Unit tests for <module>.py"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(r"c:\GHC\.github\hooks\scripts")
sys.path.insert(0, str(SCRIPTS_DIR))

from my_module import my_function


class TestMyFunction(unittest.TestCase):

    def test_XX001_description_of_what_is_tested(self):
        self.assertEqual(my_function("input"), "expected")

    def test_XX002_edge_case(self):
        self.assertIsNone(my_function(""))


if __name__ == "__main__":
    unittest.main()
```

テストIDは `TT###` 形式（`TT` = 対象モジュール略称2文字、`###` = 連番）。

## その他

- `from __future__ import annotations` を全ファイルの先頭に記述する
- ファイルパスは `str` でなく `pathlib.Path` を使う
- 文字コードは明示的に `encoding="utf-8"` を指定する
- 冗長な処理・デッドコード・使われないインポートは残さない
- コメントは「何をするか」でなく「なぜそうするか」を書く
