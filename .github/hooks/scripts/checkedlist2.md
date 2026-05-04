# フックスクリプト チェックリスト点検結果（第2回）

チェック対象: `.github/hooks/scripts/` 内の全 `.py` ファイル
チェック基準: `.github/hooks-docs/hook-template.md`
チェック実施日: 2026-05-04
前回チェック: `checkedlist.md`（修正前）

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
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ✅ | `main()` try ブロック冒頭で `DEBUG.log("input", tool_name=tool_name, docs_dir=args.docs_dir, iter_dir=args.iter_dir)` を記録。`is_write_tool()` チェックの前に実行される |
| 5 | `DEBUG.log("done", ...)` の記録 | ✅ | `DEBUG.log("done", blocked=blocked, checked=len(evaluations))` あり |
| 6 | `DEBUG.log("error", ...)` の記録 | ✅ | `except Exception as exc: DEBUG.log("error", exc=str(exc))` あり |

### 1-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ✅ | `from hook_output import HookOutput` + `OUT = HookOutput(raw.get("hookEventName") or "PreToolUse")` あり |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ✅ | ブロック時に `sys.exit(OUT.deny(reason_str))` を使用 |
| 9 | 不要時は stdout に何も出力しない | ✅ | 非書き込みツール・ターゲットなし・評価なし の各スキップパスはすべて単純 `return` |

### 1-4. セキュリティ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 10 | `tool_input` 値のバリデーション | ✅ | `is_write_tool()` でツール種別確認後に `get_written_paths()` を実行 |
| 11 | ログへのシークレット記録なし | ✅ | パス・フラグ等のデバッグ情報のみ記録 |
| 12 | プロンプトのマスキング | N/A | プロンプトを扱わない |
| 13 | 読み取りアクセス制御の実装（必要な場合） | N/A | 書き込みゲートチェック用途。読み取りアクセス制御は対象外 |

### 1-5. サマリ

| 種別 | 件数 |
|---|---|
| NG | **0件** |
| 要注意 | 0件 |
| OK | 7件 |
| 対象外 | 2件 |

> 前回 NG 5件 → **全件解消**

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
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ✅ | `main()` 冒頭で `DEBUG.log("input", tool_name=payload.get("tool_name"), cwd=workspace)` あり |
| 5 | `DEBUG.log("done", ...)` の記録 | ✅ | `_run_patch()` 内で `DEBUG.log("done", returncode=..., stdout=..., stderr=...)` あり |
| 6 | `DEBUG.log("error", ...)` の記録 | ✅ | `_run_patch()` 内の `except subprocess.TimeoutExpired` / `except OSError` でそれぞれ `DEBUG.log("error", ...)` を使用 |

### 2-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ✅ | `from hook_output import HookOutput, EXIT_OK` + `OUT = HookOutput(payload.get("hookEventName") or "PostToolUse")` あり |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ✅ | エラー時・パッチスクリプト不在時に `sys.exit(OUT.warn(...))` を使用 |
| 9 | 不要時は stdout に何も出力しない | ⚠️ | 非書き込みツール・`docs/` 外スキップは単純 `return` ✅。ただし正常完了時（`result.returncode == 0`）に `sys.exit(EXIT_OK)` を使用。機能上は stdout へ何も書かず exit 0 であり問題ないが、チェックリスト指針「何も呼ばずに `return`」とは異なるスタイル |

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
| NG | **0件** |
| 要注意 | 1件（No.9: 正常完了時 `sys.exit(EXIT_OK)` vs `return`） |
| OK | 6件 |
| 対象外 | 2件 |

> 前回 NG 5件 → **全件解消**（要注意 1件残存）

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
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ✅ | `DEBUG.log("input", event=args.event, tool_name=tool_name)` あり |
| 5 | `DEBUG.log("done", ...)` の記録 | ✅ | `DEBUG.log("done")` あり |
| 6 | `DEBUG.log("error", ...)` の記録 | ✅ | `except Exception as exc: DEBUG.log("error", exc=str(exc))` あり |

### 3-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ✅ | `from hook_output import HookOutput` + `OUT = HookOutput(args.event)` あり。このスパイフックはブロックしないため `OUT` メソッドは呼ばれないが、初期化自体は完了している |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ✅ | スパイフックはブロック・警告を行わないため `OUT.method()` 呼び出し不要。`try` ブロック正常終了後は自然な `return` で終わる |
| 9 | 不要時は stdout に何も出力しない | ✅ | `print()` / `sys.exit(OUT.method(...))` の呼び出しなし。stdout への出力なし |

### 3-4. ペイロード解析

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 14 | `read_payload()` / `parse_payload()` の使用 | ✅ | `from hook_payload import read_payload` をインポートし `payload = read_payload()` を使用 |

### 3-5. セキュリティ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 10 | `tool_input` 値のバリデーション | N/A | 全ペイロードのログ記録が目的のためバリデーション不要 |
| 11 | ログへのシークレット記録なし | ⚠️ | `DEBUG.log("spy", ..., input_payload=payload)` で**ペイロード全体**をログに記録（※ユーザーにより再追加）。`_sanitize()` は文字列長の制限のみでマスキングなし。`tool_input` 内のコマンド引数・ファイル内容等に機密情報が含まれても検知・除去できない |
| 12 | プロンプトのマスキング | N/A | UserPromptSubmit ペイロードは扱わない |
| 13 | 読み取りアクセス制御の実装（必要な場合） | N/A | 調査用途のため適用外 |

### 3-6. サマリ

| 種別 | 件数 |
|---|---|
| NG | **0件** |
| 要注意 | 1件（No.11: `input_payload=payload` でペイロード全体をログに記録） |
| OK | 6件 |
| 対象外 | 3件 |

> 前回 NG 7件・要注意 1件 → **NG 全件解消**（要注意 1件は意図的に再追加）

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
| 4 | 入力受信時に `DEBUG.log("input", ...)` を記録 | ✅ | `try` ブロック内、`isinstance` チェックの**前**で `DEBUG.log("input", hook_event=event.hook_event_name)` を記録。全イベント種別で記録される |
| 5 | `DEBUG.log("done", ...)` の記録 | ✅ | `DEBUG.log("done")` あり（`try` ブロック末尾） |
| 6 | `DEBUG.log("error", ...)` の記録 | ✅ | `except Exception as exc: DEBUG.log("error", exc=str(exc))` あり |

### 4-3. 出力制御

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 7 | `HookOutput` のインポートと初期化 | ✅ | `from hook_output import HookOutput` + `OUT = HookOutput(event.hook_event_name or "PreToolUse")` あり |
| 8 | `sys.exit(OUT.method(...))` パターンの使用 | ✅ | コメントで全使用パターンを明示（テンプレート未実装部分は許容） |
| 9 | 不要時は stdout に何も出力しない | ✅ | 何も出力せず終了 |

### 4-4. セキュリティ

| # | チェック項目 | 結果 | 詳細 |
|---|---|---|---|
| 10 | `tool_input` 値のバリデーション | ⚠️ | テンプレートとして `is_write_tool()` / `is_read_tool()` のコメント例はあるが、バリデーション実装が必要であることを明示したコメントなし。コピー先スクリプトでの実装漏れリスクあり |
| 11 | ログへのシークレット記録なし | ✅ | テンプレートは記録なし |
| 12 | プロンプトのマスキング | N/A | テンプレートはプロンプト扱いなし |
| 13 | 読み取りアクセス制御の実装（必要な場合） | ✅ | `is_read_tool()` + `get_read_paths()` のコメント例あり |

### 4-5. サマリ

| 種別 | 件数 |
|---|---|
| NG | **0件** |
| 要注意 | 1件（No.10: バリデーション必要性の明示コメントなし） |
| OK | 8件 |
| 対象外 | 1件 |

> 前回 NG 2件 → **全件解消**（要注意 1件は前回から継続）

---

## 5. ライブラリファイル（チェックリスト対象外）

セキュリティ観点のみ確認。前回からの変更なし。

| ファイル | セキュリティ観点 | 結果 |
|---|---|---|
| `debug_logging.py` | ログパスはスクリプトディレクトリ配下に固定 | ✅ |
| `hook_output.py` | `json.dumps()` 使用によりインジェクション防止 | ✅ |
| `hook_payload.py` | 不正 JSON は `{}` として扱う | ✅ |
| `tool_input.py` | パストラバーサルは呼び出し元の責任 | ⚠️ |

---

## 全体サマリ

| スクリプト | 前回 NG | 今回 NG | 前回 ⚠️ | 今回 ⚠️ |
|---|---|---|---|---|
| `check_phase_gate.py` | 5 | **0** | 0 | 0 |
| `post_tool_dashboard_sync.py` | 5 | **0** | 0 | 1 |
| `tool_input_spy.py` | 7 | **0** | 1 | 1 |
| `hook-template.py` | 2 | **0** | 1 | 1 |

### 残存 要注意事項

| スクリプト | No. | 内容 | 経緯 |
|---|---|---|---|
| `post_tool_dashboard_sync.py` | 9 | 正常完了時に `sys.exit(EXIT_OK)` を使用。stdout 無出力であり機能上問題ないが、チェックリスト指針「何も呼ばずに `return`」とスタイルが異なる | 今回新規発生 |
| `tool_input_spy.py` | 11 | `DEBUG.log("spy", ..., input_payload=payload)` でペイロード全体をログに記録。マスキングなし | 前回から継続。ユーザーにより意図的に再追加 |
| `hook-template.py` | 10 | バリデーション実装が必要であることを明示したコメントなし | 前回から継続 |

### 総評

**前回 NG 合計 19件 → 今回 0件**。全 NG が解消された。残存の要注意 3件はいずれも機能的に問題のないスタイル・セキュリティ判断の差異であり、`tool_input_spy.py` の `input_payload=payload` についてはユーザーが意図的に再追加したものである。
