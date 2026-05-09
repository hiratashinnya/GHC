# unittest テストパターン

テストは `unittest.TestCase` を使う。`pytest` は使わない。
テストIDは `TT###` 形式（`TT` = 対象モジュール略称2文字、`###` = 連番）。

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
