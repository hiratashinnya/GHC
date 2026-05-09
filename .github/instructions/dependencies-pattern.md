# 依存関係パターン

標準ライブラリのみ使用し、外部パッケージは禁止。

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
