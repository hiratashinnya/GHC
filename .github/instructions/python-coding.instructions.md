---
description: "Use when writing, editing, or reviewing Python scripts in this workspace. Enforces standard-library-only, dataclass-based type-safe design, unittest, thin main(), single-responsibility, and project-specific doc-style. Trigger phrases: python script, write python, hook script, lib module, python coding style, python implementation"
applyTo: "**/*.py"
---

# Python コーディング規約

## 依存関係

- **標準ライブラリのみ使用する。**`pip install` は禁止。
- 必要なサードパーティ機能は標準ライブラリで代替するか、プロジェクト内の `_lib/` モジュールを使う。

→ コード例: [dependencies-pattern.md](dependencies-pattern.md)

## データ構造：dataclass を使う

`dict` や `tuple` の多用は禁止。複数フィールドを持つデータは必ず `@dataclass` で定義する。
`field(default_factory=...)` を使い、KeyError を起こさない安全なデフォルトを設定する。
複数フィールドをキー文字列でルーティングするロジックは dataclass 自身のメソッドとして持つ。

→ コード例: [dataclass-pattern.md](dataclass-pattern.md) / ルーティング: [dataclass-routing-pattern.md](dataclass-routing-pattern.md)

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

→ コード例: [validation-pattern.md](validation-pattern.md)

## main() の設計：薄く、1画面で意図が分かるように

`main()` は **オーケストレーション専用**。ロジックを直書きしない。
1画面（約30行以内）で「何をするスクリプトか」が読み取れるようにする。

→ コード例: [main-pattern.md](main-pattern.md)

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
関数レベルも同じ4項目（責務・入力・出力・副作用）を簡潔に記述する。

→ テンプレート: [docstring-pattern.md](docstring-pattern.md)

## テスト：unittest

テストは `unittest.TestCase` を使う。`pytest` は使わない。
テストIDは `TT###` 形式（`TT` = 対象モジュール略称2文字、`###` = 連番）。

→ テンプレート: [unittest-pattern.md](unittest-pattern.md)

## その他

- `from __future__ import annotations` を全ファイルの先頭に記述する
- ファイルパスは `str` でなく `pathlib.Path` を使う
- 文字コードは明示的に `encoding="utf-8"` を指定する
- 冗長な処理・デッドコード・使われないインポートは残さない
- コメントは「何をするか」でなく「なぜそうするか」を書く
