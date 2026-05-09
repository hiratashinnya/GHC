# dataclass 基本パターン

## dict/tuple の代わりに @dataclass を使う

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

## デフォルト値には field(default_factory=...) を使う

ミュータブルなデフォルト値には `field(default_factory=...)` を使い、
KeyError を起こさない安全なデフォルトを設定する。

```python
from dataclasses import dataclass, field

@dataclass
class HookPayload:
    tool_name: str = ""
    tool_input: dict = field(default_factory=dict)
```

## キーによるフィールドルーティング

複数フィールドをキー文字列でルーティングするロジックは dataclass 自身のメソッドとして持つ。
→ [dataclass-routing-pattern.md](dataclass-routing-pattern.md)
