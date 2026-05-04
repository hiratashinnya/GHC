# フックスクリプト チェックリスト点検結果

チェック対象: `.github/hooks/scripts/` 内の全 `.py` ファイル
チェック基準: `.github/hooks-docs/hook-template.md`
チェック実施日: 2026-05-04
対象commit: 4c1c09ac909c411fb4ed52ef35a2c9d5dfc748e7

---

## 凡例

| 記号 | 意味 |
|---|---|
| ✅ | OK — 要件を満たしている |
| ❌ | NG — 未対応または違反 |
| ⚠️ | 要注意 — 機能するが改善推奨 |
| N/A | 対象外 — スクリプト用途上適用しない / ライブラリのため不適用 |

---

## スクリプト分類

| ファイル | 種別 | 備考 |
|---|---|---|
| `check_phase_gate.py` | フックスクリプト | PreToolUse 書き込みゲートチェック |
| `post_tool_dashboard_sync.py` | フックスクリプト | PostToolUse ダッシュボード同期 |
| `tool_input_spy.py` | フックスクリプト（調査用） | Pre/PostToolUse 全ツールログ |
| `hook-template.py` | テンプレート | 新規スクリプト作成時のコピー元 |
| `debug_logging.py` | ライブラリ | チェックリスト適用外 |
| `hook_output.py` | ライブラリ | チェックリスト適用外 |
| `hook_payload.py` | ライブラリ | チェックリスト適用外 |
| `tool_input.py` | ライブラリ | チェックリスト適用外 |

---

## 1. `check_phase_gate.py`

**役割**: PreToolUse フック。`docs/` / `iter/` への書き込み前にフェーズゲート承認を確認し、未承認の場合はブロックする。

### 1-1. 基本構造

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 1 | `HookDebugLogger` の初期化 | ✅ | `DEBUG = HookDebugLogger(SCRIPT_DIR, "check_phase_gate")` |
| 2 | デバッグフラグファイル名 | ✅ | `check_phase_gate.debug`（ライブラリ自動管理） |
| 3 | ログファイル名 | ✅ | `check_phase_gate.debug.log`（ライブラリ自動管理） |

### 1-2. デバッグログ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ❌ | `main()` 冒頭で `DEBUG.log("start", ...)` を使用。ラベルが `"input"` ではなく `"start"` |
| 5 | `DEBUG.log("done", ...)` の記録 | ✅ | `DEBUG.log("done", blocked=blocked, checked=len(evaluations))` あり |
| 6 | `DEBUG.log("error", ...)` の記録 | ❌ | 例外処理ブロック（try/except）がなく、エラーログの仕組みなし |

### 1-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ❌ | `from hook_output import HookOutput` なし。`OUT` オブジェクト未作成 |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ❌ | `out_json(payload)` + `sys.exit(2)` を直接使用。`HookOutput` 経由でない |
| 9 | 不要時は stdout に何も出力しない | ❌ | 非書き込みツールスキップ時に `out_json({"success": True, ...})` を出力してから `return`。stdout 原則違反 |

### 1-4. セキュリティ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 10 | `tool_input` 値のバリデーション | ✅ | `is_write_tool()` でツール種別を確認後にパス処理 |
| 11 | ログへのシークレット記録なし | ✅ | パス・フラグ等のデバッグ情報のみ記録 |
| 12 | プロンプトのマスキング | N/A | プロンプトを扱わない |
| 13 | 読み取りアクセス制御の実装（必要な場合） | N/A | 書き込みゲートチェック用途。読み取りアクセス制御は対象外 |

### 1-5. サマリ

| 種別 | 件数 |
|---|---|
| NG | 5件（No.4, 6, 7, 8, 9） |
| 要注意 | 0件 |
| OK | 5件 |
| 対象外 | 2件 |

---

## 2. `post_tool_dashboard_sync.py`

**役割**: PostToolUse フック。書き込みツールが `docs/*.md` を変更した場合のみ、`patch_dashboard.py` を起動してダッシュボードを同期する。

### 2-1. 基本構造

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 1 | `HookDebugLogger` の初期化 | ✅ | `DEBUG = HookDebugLogger(SCRIPT_DIR, "post_tool_dashboard_sync")` |
| 2 | デバッグフラグファイル名 | ✅ | `post_tool_dashboard_sync.debug`（ライブラリ自動管理） |
| 3 | ログファイル名 | ✅ | `post_tool_dashboard_sync.debug.log`（ライブラリ自動管理） |

### 2-2. デバッグログ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ❌ | `main()` 冒頭には入力ログなし。`_extract_changed_file()` 内に `DEBUG.log("tool_input_keys", ...)` はあるが、エントリポイントでの `"input"` ラベルでの記録が不在 |
| 5 | `DEBUG.log("done", ...)` の記録 | ✅ | `_run_patch()` 内で `DEBUG.log("done", returncode=..., stdout=..., stderr=...)` あり |
| 6 | `DEBUG.log("error", ...)` の記録 | ❌ | エラー系のログは `"timeout"` / `"launch_error"` ラベルを使用。チェックリスト指定の `"error"` ラベルを使用していない |

### 2-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ❌ | `from hook_output import HookOutput` なし。`OUT` オブジェクト未作成 |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ❌ | `out_json({"continue": True, ...})` を直接使用。`HookOutput` 経由でない |
| 9 | 不要時は stdout に何も出力しない | ❌ | 非書き込みツールスキップ時・`docs/` 外ファイルスキップ時に `out_json({"continue": True})` を出力。stdout 原則（不要な場合は何も出力しない）に違反 |

### 2-4. セキュリティ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 10 | `tool_input` 値のバリデーション | ✅ | `is_write_tool()` + `_is_docs_md()` でパスを検証 |
| 11 | ログへのシークレット記録なし | ✅ | コマンドプレビュー・リターンコード等のみ記録 |
| 12 | プロンプトのマスキング | N/A | プロンプトを扱わない |
| 13 | 読み取りアクセス制御の実装（必要な場合） | N/A | PostToolUse ダッシュボード同期用途。読み取りアクセス制御は対象外 |

### 2-5. サマリ

| 種別 | 件数 |
|---|---|
| NG | 5件（No.4, 6, 7, 8, 9） |
| 要注意 | 0件 |
| OK | 5件 |
| 対象外 | 2件 |

---

## 3. `tool_input_spy.py`

**役割**: 調査用スパイフック。Pre/PostToolUse の全ツール呼び出しを `tool_input_spy.debug.log` に記録する。常に続行し、決してブロックしない。

### 3-1. 基本構造

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 1 | `HookDebugLogger` の初期化 | ✅ | `DEBUG = HookDebugLogger(SCRIPT_DIR, "tool_input_spy")` |
| 2 | デバッグフラグファイル名 | ✅ | `tool_input_spy.debug`（ライブラリ自動管理） |
| 3 | ログファイル名 | ✅ | `tool_input_spy.debug.log`（ライブラリ自動管理） |

### 3-2. デバッグログ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ❌ | `DEBUG.log("spy", ...)` ラベルを使用。ラベルが `"input"` ではない |
| 5 | `DEBUG.log("done", ...)` の記録 | ❌ | `DEBUG.log("done", ...)` なし。ログ記録後にそのまま終了 |
| 6 | `DEBUG.log("error", ...)` の記録 | ❌ | `_read_stdin()` の `except OSError` でエラーログなし。エラー時にサイレントで `None` を返す |

### 3-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ❌ | `from hook_output import HookOutput` なし |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ❌ | `print(json.dumps({"continue": True}, ensure_ascii=False))` を直接使用 |
| 9 | 不要時は stdout に何も出力しない | ❌ | スパイは常にログ記録のみが目的のため stdout 出力は不要。`{"continue": True}` を毎回出力している |

### 3-4. ペイロード解析

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 14 | `read_payload()` / `parse_payload()` の使用 | ❌ | 独自実装の `_read_stdin()` を使用。`hook_payload.py` のライブラリを使っていない |

### 3-5. セキュリティ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 10 | `tool_input` 値のバリデーション | N/A | 全ペイロードのログ記録が目的のためバリデーション不要 |
| 11 | ログへのシークレット記録なし | ⚠️ | `input_payload=payload` で**ペイロード全体**をログに記録。`tool_input` 内のコマンド引数やファイル内容等に機密情報が含まれても検知できない。`_sanitize()` は文字列長の制限のみでマスキングなし |
| 12 | プロンプトのマスキング | N/A | UserPromptSubmit ペイロードは扱わない |
| 13 | 読み取りアクセス制御の実装（必要な場合） | N/A | 調査用途のため適用外 |

### 3-6. サマリ

| 種別 | 件数 |
|---|---|
| NG | 7件（No.4, 5, 6, 7, 8, 9, 14） |
| 要注意 | 1件（No.11） |
| OK | 3件 |
| 対象外 | 2件 |

---

## 4. `hook-template.py`

**役割**: 新規フックスクリプト作成時のコピー元テンプレート。実装のプレースホルダーを含む。

### 4-1. 基本構造

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 1 | `HookDebugLogger` の初期化 | ✅ | `DEBUG = HookDebugLogger(SCRIPT_DIR, "<script_name>")` |
| 2 | デバッグフラグファイル名 | ✅ | 自動管理 |
| 3 | ログファイル名 | ✅ | 自動管理 |

### 4-2. デバッグログ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ❌ | `isinstance(event, PreToolUsePayload)` のブロック内にのみ `DEBUG.log("input", ...)` が存在。PostToolUse・SessionStart 等の他イベントでは入力ログが記録されない |
| 5 | `DEBUG.log("done", ...)` の記録 | ✅ | `main()` 末尾に `DEBUG.log("done")` あり |
| 6 | `DEBUG.log("error", ...)` の記録 | ❌ | 例外処理ブロック（try/except）がなく、エラーログの仕組みなし |

### 4-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ✅ | インポート・`OUT = HookOutput(event.hook_event_name or "PreToolUse")` 初期化あり |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ✅ | コメントで使用パターンを明示（テンプレート未実装部分は許容） |
| 9 | 不要時は stdout に何も出力しない | ✅ | `DEBUG.log("done")` のみで終了。stdout への出力なし |

### 4-4. セキュリティ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 10 | `tool_input` 値のバリデーション | ⚠️ | テンプレートとして触れていない。コピー先スクリプトで実装が必要だが、チェックリスト項目としての明示コメントなし |
| 11 | ログへのシークレット記録なし | ✅ | テンプレートは記録なし |
| 12 | プロンプトのマスキング | N/A | テンプレートはプロンプト扱いなし |
| 13 | 読み取りアクセス制御の実装（必要な場合） | ✅ | `is_read_tool()` + `get_read_paths()` のコメント例あり |

### 4-5. サマリ

| 種別 | 件数 |
|---|---|
| NG | 2件（No.4, 6） |
| 要注意 | 1件（No.10） |
| OK | 8件 |
| 対象外 | 1件 |

---

## 5. ライブラリファイル（チェックリスト対象外）

以下のファイルはフックスクリプトではなくライブラリのため、チェックリストの基本構造・デバッグログ・出力制御の項目は適用外とする。
セキュリティ観点のみ確認する。

### `debug_logging.py`

| 観点 | 結果 | 詳細 |
|---|---|---|
| セキュリティ（外部入力のバリデーション） | ✅ | ログパスはスクリプトディレクトリ配下に固定。外部入力でパスが変わらない |
| シークレット記録 | ✅ | ライブラリ自体はシークレットを扱わない。記録内容は呼び出し元の責任 |

### `hook_output.py`

| 観点 | 結果 | 詳細 |
|---|---|---|
| セキュリティ（外部入力のバリデーション） | ✅ | 出力文字列は呼び出し元が渡す。バリデーション責任は呼び出し元 |
| JSON インジェクション | ✅ | `json.dumps()` を使用。文字列はエスケープされる |

### `hook_payload.py`

| 観点 | 結果 | 詳細 |
|---|---|---|
| セキュリティ（外部入力のバリデーション） | ✅ | stdin を JSON パースするのみ。不正 JSON は `{}` として扱う |
| デフォルト値 | ✅ | 全フィールドにデフォルト値設定。欠損キーで `KeyError` が起きない |

### `tool_input.py`

| 観点 | 結果 | 詳細 |
|---|---|---|
| セキュリティ（外部入力のバリデーション） | ✅ | パス抽出のみ。バリデーション責任は呼び出し元 |
| パストラバーサル | ⚠️ | `get_written_paths()` / `get_read_paths()` は返却した文字列のパストラバーサル（`../` 等）をチェックしない。呼び出し元でのバリデーションが必要 |

---

## 全体サマリ

| スクリプト | NG件数 | 要注意件数 |
|---|---|---|
| `check_phase_gate.py` | 5 | 0 |
| `post_tool_dashboard_sync.py` | 5 | 0 |
| `tool_input_spy.py` | 7 | 1 |
| `hook-template.py` | 2 | 1 |

### 共通 NG パターン

以下の3点は、`check_phase_gate.py`・`post_tool_dashboard_sync.py`・`tool_input_spy.py` の全てに共通している:

1. **`HookOutput` 未使用** — `out_json(...)` や `print(json.dumps(...))` を直接使用
2. **`sys.exit(OUT.method(...))` パターン未適用**
3. **不要時の stdout 出力** — 処理を続行するだけの場合でも `{"continue": True}` 等を出力している

### 重大度の高い個別 NG

| スクリプト | 項目 | 理由 |
|---|---|---|
| `tool_input_spy.py` No.11 | 全ペイロードをマスキングなしでログ記録 | コマンド引数・ファイルパス等に機密情報が含まれる場合にログに残存 |
| `tool_input_spy.py` No.14 | `read_payload()` 未使用 | ライブラリ整備の恩恵を受けていない |
| `hook-template.py` No.4 | PreToolUsePayload 以外で入力ログ欠落 | テンプレートから作成した PostToolUse 等のスクリプトで入力記録が漏れる |
