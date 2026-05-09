# main() 設計パターン

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
