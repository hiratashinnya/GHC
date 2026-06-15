---
name: coverage-html-report
description: Generate a coverage HTML report for the GHC TestHooks test suite using unittest (standard library only). Run coverage measurement with `python -m unittest discover`, then output to coverage_html_report/. Use when you want to measure test coverage and produce a browsable HTML report. NOT for writing test cases (see test-strategy), NOT for running tests without coverage.
---

# カバレッジ HTML レポート生成（GHC）

テストランナーは **`python -m unittest`**（標準ライブラリのみ・Q5 準拠）。
`coverage` ライブラリでカバレッジを計測し、`coverage_html_report/` に HTML 出力する。

## 前提

| 項目 | 値 |
|---|---|
| テストディレクトリ | `TestHooks/` |
| テストファイルパターン | `test_*.py` |
| 出力ディレクトリ | `coverage_html_report/` |
| ランナー | `python -m unittest discover` |

## 手順

```bash
# 1. coverage がなければインストール
pip install coverage

# 2. カバレッジ計測つきでテストを実行
python -m coverage run -m unittest discover -s TestHooks -p "test_*.py" -v

# 3. HTMLレポートを生成
python -m coverage html --directory=coverage_html_report

# 4. coverage が自動生成する .gitignore を削除（コミット対象にするため）
rm -f coverage_html_report/.gitignore

# 5. サマリーをターミナルに表示
python -m coverage report
```

## コミット対象

| ファイル | 用途 |
|---|---|
| `.coverage` | 計測データ（バイナリ） |
| `coverage_html_report/` | HTMLレポート一式 |

## done

- `coverage_html_report/index.html` が生成されているか。
- `python -m coverage report` で総カバレッジ率が表示されるか。
- `.coverage` と `coverage_html_report/` がコミット済みか。
