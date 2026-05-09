# 自己検証パターン（実行時 assert / 事後条件）

境界値・型・不変条件は `assert` または早期 `raise` で明示する。
サイレントに壊れたデータを返さない。

```python
def phase_index(phase: str) -> int:
    if phase not in PHASE_INDEX:
        raise ValueError(f"Unknown phase: {phase!r}")
    return PHASE_INDEX[phase]
```
