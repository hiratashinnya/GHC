# testresult: access_control hook

対象スクリプト: `.github/hooks/scripts/entrypoints/access_control.py`
関連モジュール: `ac_config_loader.py`, `ac_rule_engine.py`
実行日: 2026-05-21
コミットID: e4b618f
実行コマンド: `cd TestHooks/access_control && python -m unittest test_access_control -v`
総合結果: **FAIL** (88/90, failures=2)

---

## テスト結果

| テストID | クラス | 観点 | 結果 | 判定 |
|----------|--------|------|------|------|
| AC-001 | TestLoadConfig | `load_config` 正常読み込み | `AccessControlConfig` 返却、各 rules 格納 | PASS |
| AC-001b | TestLoadConfig | 配列形式 backward compat | `RuleGroup(enabled=True, rules=[...])` として返却 | PASS |
| AC-002 | TestLoadConfig | `load_config` 不正 action のルールをスキップ | 不正ルールスキップ、有効ルール1件残存 | PASS |
| AC-003 | TestLoadConfig | `load_config` ファイル不在 | `FileNotFoundError` 送出 | PASS |
| AC-003b | TestLoadConfig | `load_config` JSON 構文エラー | `json.JSONDecodeError` 送出 | PASS |
| AC-004 | TestLoadConfig | `load_config` ルール空配列 | `rules=[]` の `RuleGroup` を返す | PASS |
| AC-005 | TestLoadConfig | `Rule.is_active()` disabled | `False` を返す | PASS |
| AC-006 | TestLoadConfig | `_parse_when` path_patterns | `WhenClause.path_patterns` に格納 | PASS |
| AC-007 | TestLoadConfig | `_parse_when` command_patterns | `WhenClause.command_patterns` に格納 | PASS |
| AC-008 | TestEnabledDisable | グローバル `enabled=False` → 全ルール無効 | `None` | PASS |
| AC-008a | TestLoadConfig | `_parse_when` scope_patterns | `WhenClause.scope_patterns` に格納 | PASS |
| AC-008b | TestLoadConfig | `_parse_when` path_patterns + scope_patterns | 両フィールドに正しく格納 | PASS |
| AC-010 | TestEvaluateWriteRules | write: ルールなし → allow | `None` | PASS |
| AC-011 | TestEvaluateWriteRules | write: パスマッチ → deny | deny `RuleMatch` | PASS |
| AC-012 | TestEvaluateWriteRules | write: パスマッチ → confirm | confirm `RuleMatch` | PASS |
| AC-013 | TestEvaluateWriteRules | write: パス不一致 → allow | `None` | PASS |
| AC-014 | TestEvaluateWriteRules | write: disabled → allow | `None` | PASS |
| AC-015 | TestEvaluateWriteRules | write: deny > confirm 優先 | deny `RuleMatch` | PASS |
| AC-016 | TestEvaluateWriteRules | `replace_string_in_file` パスマッチ | deny を返す | PASS |
| AC-017 | TestEvaluateWriteRules | `multi_replace_string_in_file` 複数パス | deny（1件マッチで発動） | PASS |
| AC-020 | TestEvaluateReadRules | read: ルールなし → allow | `None` | PASS |
| AC-021 | TestEvaluateReadRules | read: `.env` → deny（`**/` prefix 正規化） | deny を返す | PASS |
| AC-022 | TestEvaluateReadRules | read: `list_dir` パス不一致 → allow | `None` | PASS |
| AC-023 | TestEvaluateReadRules | read: path_patterns 未指定 → 全マッチ | deny を返す | PASS |
| AC-140 | TestEvaluateReadRules | read: 全体 grep scope が保護 `.env` スコープを包含 | deny を返す | PASS |
| AC-141 | TestEvaluateReadRules | read: 親 subtree grep が子保護 subtree を包含 | deny を返す | PASS |
| AC-142 | TestEvaluateReadRules | read: `src/**` と `src/**/*.env` の不確実交差 | confirm を返す | PASS |
| AC-143 | TestEvaluateReadRules | read: `docs/**` と保護 scope 群は明確非交差 | `None` | PASS |
| AC-144 | TestEvaluateReadRules | read: 空 includePattern は ambiguous 扱い | confirm を返す | PASS |
| AC-145 | TestEvaluateReadRules | read: file_search 全体 query が `*.secret` を包含 | deny を返す | PASS |
| AC-146 | TestEvaluateReadRules | read: concrete path match が scope match より先に効く | deny を返す | PASS |
| AC-147 | TestEvaluateReadRules | read: scope_patterns 未指定時の path_patterns 後方互換 | deny を返す | PASS |
| AC-030 | TestEvaluateCommandRules | command: ルールなし → allow | `None` | PASS |
| AC-031 | TestEvaluateCommandRules | command: `rm -rf` → deny | deny を返す | PASS |
| AC-032 | TestEvaluateCommandRules | command: 大小文字無視マッチ | deny を返す | PASS |
| AC-033 | TestEvaluateCommandRules | command: パターン不一致 → allow | `None` | PASS |
| AC-034 | TestEvaluateCommandRules | command: `git push --force` → deny | deny を返す | PASS |
| AC-036 | TestEvaluateCommandRules | command: settings false 由来の危険パターン → deny（11種サブテスト） | 全サブテスト deny を返す | PASS |
| AC-038 | TestEvaluateCommandRules | command: pip/conda/poetry install → deny | 全サブテスト deny を返す | PASS |
| AC-039 | TestEvaluateCommandRules | command: git push / git clone → deny | 全サブテスト deny を返す | PASS |
| AC-042 | TestEvaluateCommandRules | command: PowerShell/Linux/Node package install commands → deny | 全サブテスト deny を返す | PASS |
| AC-035 | TestEvaluateCommandRules | command: command_patterns 未指定 → 全マッチ | deny を返す | PASS |
| AC-040 | TestUnknownTools | 未分類ツール `semantic_search` → allow | `None` | PASS |
| AC-041 | TestUnknownTools | 未分類ツール `grep_search` → allow | `None` | PASS |
| AC-050 | TestPathNormalization | Windows絶対パス → 相対化 → `docs/**` マッチ | `AssertionError: unexpectedly None` | FAIL |
| AC-051 | TestPathNormalization | cwd外パス → 相対化せず → マッチしない | `None` | PASS |
| AC-060 | TestEnabledDisable | `write_rules.enabled=False` → write ルール無効 | `None` | PASS |
| AC-061 | TestEnabledDisable | `read_rules.enabled=False` → read ルール無効 | `None` | PASS |
| AC-062 | TestEnabledDisable | `command_rules.enabled=False` → command ルール無効 | `None` | PASS |
| AC-070 | TestGetGroup | `get_group("write")` → write_rules を返す | `rules[0].rule_id == "r1"` | PASS |
| AC-071 | TestGetGroup | `get_group("read")` → read_rules を返す | `rules[0].rule_id == "r2"` | PASS |
| AC-072 | TestGetGroup | `get_group("command")` → command_rules を返す | `rules[0].rule_id == "r3"` | PASS |
| AC-073 | TestGetGroup | `get_group` 未知タイプ → 空 RuleGroup | `RuleGroup(rules=[])` | PASS |
| AC-080 | TestBuildConfigWarning | `skipped_rules` 空 → `""` | `""` を返す | PASS |
| AC-081 | TestBuildConfigWarning | `skipped_rules` あり → `"⚠"` で始まる文字列 | `"⚠"` で始まる文字列 | PASS |
| AC-082 | TestLoadConfigOrExit | FileNotFoundError → event.warn() + sys.exit(0) | event.warn() 呼び出し後 sys.exit(0) | PASS |
| AC-083 | TestLoadConfigOrExit | Exception → event.warn() + sys.exit(0) | event.warn() にエラー文字列を含む、sys.exit(0) | PASS |
| AC-084 | TestLoadConfigOrExit | 正常読み込み → config を返す | config オブジェクトを返す（sys.exit なし） | PASS |
| AC-085 | TestDispatchAction | result=None + warning='' → sys.exit なし | sys.exit なし、event メソッド未呼び出し | PASS |
| AC-086 | TestDispatchAction | result=None + warning あり → sys.exit(warn) | event.warn() 呼び出し後 sys.exit(0) | PASS |
| AC-087 | TestDispatchAction | action='deny' → sys.exit(2) | event.deny() 呼び出し後 sys.exit(2) | PASS |
| AC-088 | TestDispatchAction | action='deny' + warning → reason に warning 付加 | deny の reason 引数に warning を含む | PASS |
| AC-089 | TestDispatchAction | action='confirm' → sys.exit(ask) | event.ask() 呼び出し後 sys.exit(0) | PASS |
| AC-090 | TestDispatchAction | action='allow' + warning='' → sys.exit なし | sys.exit なし | PASS |
| AC-091 | TestDispatchAction | action='allow' + warning あり → sys.exit(warn) [リグレッション] | event.warn() 呼び出し後 sys.exit(0) | PASS |
| AC-092 | TestCommandPatternRegex | `git add` が `\\bdd\\b` に誤マッチしない | `[]` を返す | PASS |
| AC-093 | TestCommandPatternRegex | `dd if=/dev/zero` が `\\bdd\\b` にマッチ | `['\\bdd\\b']` を返す | PASS |
| AC-093b | TestCommandPatternRegex | `deadline-...` が `\\bdd\\b` に非マッチ | `[]` を返す | PASS |
| AC-094 | TestCommandPatternRegex | 無効 regex は skip し debug ログ記録 | 無効パターンは結果に含まれず、`debug.log()` 呼び出し | PASS |
| AC-095 | TestCommandPatternRegex | 複数 regex のマッチ結果を返す | `\\brm\\b` が含まれる結果を返す | PASS |
| AC-096 | TestCommandPatternRegex | regex マッチは大小文字無視 | `['\\bDD\\b']` を返す | PASS |
| AC-100 | TestGetWritePaths | apply_patch: Update File パスを抽出 | `["c:\\GHC\\docs\\foo.md"]` を返す | PASS |
| AC-101 | TestGetWritePaths | apply_patch: 複数 File 行を抽出 | 両パスをリストで返す | PASS |
| AC-102 | TestGetWritePaths | apply_patch: rename の source パスのみ返す | `["old.py"]` を返す | PASS |
| AC-103 | TestGetWritePaths | apply_patch: input が非文字列 → 空リスト | `[]` を返す | PASS |
| AC-104 | TestGetWritePaths | create_directory: dirPath を返す | `["src/subdir"]` を返す | PASS |
| AC-105 | TestGetWritePaths | 非 write ツール → 空リスト | `[]` を返す | PASS |
| AC-110 | TestGetReadPaths | read_file: filePath を返す | `["docs/foo.md"]` を返す | PASS |
| AC-111 | TestGetReadPaths | get_errors: filePaths リストを返す | `["a.py", "b.py"]` を返す | PASS |
| AC-112 | TestGetReadPaths | grep_search: includePattern を返す | `["src/**/*.py"]` を返す | PASS |
| AC-113 | TestGetReadPaths | 非 read ツール → 空リスト | `[]` を返す | PASS |
| AC-120 | TestGetCommandString | command キー直接参照 | `"git status"` を返す | PASS |
| AC-121 | TestGetCommandString | task.command + task.args を合成 | `"python -m pytest"` を返す | PASS |
| AC-122 | TestGetCommandString | task.args 空 → コマンドのみ | `"python"` を返す | PASS |
| AC-123 | TestGetCommandString | キーなし → 空文字 | `""` を返す | PASS |
| AC-130 | TestEvaluateViaParser | apply_patch パスが deny ルールにマッチ | `AssertionError: unexpectedly None` | FAIL |
| AC-131 | TestEvaluateViaParser | create_and_run_task コマンドが deny ルールにマッチ | deny を返す | PASS |
| AC-132 | TestEvaluateViaParser | send_to_terminal が command ツールとして評価 | deny を返す | PASS |
| AC-133 | TestEvaluateViaParser | grep_search includePattern は `**/.env` ルールにマッチ | deny を返す | PASS |
| AC-134 | TestEvaluateViaParser | workspace 外絶対パスが評価対象から漏れない | deny を返す | PASS |

### 備考付きサマリ

| テストID | 判定 | 備考 |
|----------|------|------|
| AC-133 | 初回FAIL → 再実行PASS | 初回実行（79/80）では `includePattern=".env"` が `**/.env` にマッチして deny となり期待値 `None` と不一致。方針決定後に testcase/test を修正して再実行（80/80）でPASS。 |

### 失敗詳細

| 項目 | 内容 |
|------|------|
| テストID | AC-133 |
| 初回実行（失敗） | 実行日: 2026-05-18 / コミット: `8ec1052` / 結果: FAIL (79/80) |
| 失敗時の期待値 | `None` |
| 失敗時の実際値 | deny の `RuleMatch`（`includePattern=".env"` が `**/.env` にマッチ） |
| 失敗原因 | テスト設計（期待値）と実装方針（`includePattern` を read 評価対象に含める）が不一致 |
| 対処内容 | 1) `TestHooks/access_control/testcase.md` の AC-133 期待値を deny に修正 2) `TestHooks/access_control/test_access_control.py` の AC-133 を deny 想定に修正 3) `tool_input_parser.py` は read-path 抽出仕様を維持 |
| 対処理由（意思決定） | ユーザー判断として「現行実装（`includePattern` を read 評価対象として扱う）を正」と確定したため。実装を変えるのではなく、仕様・テスト期待値を実装方針へ整合させた。 |
| 判断根拠 | 実測で `includePattern=".env"` は `**/.env` にマッチし deny。機密ファイル探索の誤許可を防ぐ保守的方針（fail-closed）と整合。 |
| 却下した案 | `grep_search.includePattern` を read path から除外する案（スコープ情報扱い）は、現行セキュリティ方針と不整合のため今回不採用。 |
| 再実行（解消確認） | 実行日: 2026-05-18 / コミット: `998f043` / 結果: PASS (80/80) |
| 次アクション | 「あるべき姿」検討で、最小変更案と厳密版（scope_patterns 導入）を比較し最終方針を決定する |

---

## 修正記録

| # | テストID | 問題 | 修正内容 |
|---|----------|------|----------|
| 1 | AC-021 | `fnmatch(".env", "**/.env")` が `/` なしで不一致 | `_match_single_path()` を追加し、`**/` プレフィックスのパターンはルート直下ファイルにも適用するよう修正 |
| 2 | AC-001〜007 | `AccessControlConfig` の `write_rules` 等が `List[Rule]` → `RuleGroup` に変更 | テスト全件を `.write_rules.rules[0]` 形式に更新、`_make_config()` を `RuleGroup` を返すよう更新 |
| 3 | AC-004 | `test_AC004` の `def` ヘッダが欠落し AC-003b 内に混入していた | `def test_AC004_empty_rules(self):` ヘッダを独立したメソッドとして復元 |
| 4 | — | `_get_candidate_rules` が `AccessControlConfig` のフィールド名を直接知っていた（凝集度違反） | `AccessControlConfig.get_group()` メソッドを追加し、`_get_candidate_rules` を thin adapter に変更 |
| 5 | AC-036 | `find -delete` パターンが `find . -delete` にサブストリング不一致 | テストパターンを ` -delete` に修正（access-control.json と整合） |
| 6 | AC-038/AC-039 | `git push` 全般・`git clone`・外部ライブラリインストールのブロック要件を追加 | `access-control.json` に `git push ` / `git clone` / `deny-package-install` を追加し、テストケースとユニットテストを拡張 |
| 7 | AC-042 | PowerShell/Linux/Node 系インストールコマンドの未カバーを追加対応 | `deny-package-install` に `Install-Module` / `Install-Package` / `winget` / `apt` / `yum` / `dnf` / `pacman` / `zypper` / `apk` / `brew` / `snap` / `npm install` / `yarn add` / `pnpm add` を追加しテストを拡張 |
| 8 | AC-092〜AC-096 | コマンドパターンの部分一致で `git add` が `dd` と誤判定されるリスク | `ac_rule_engine.py` を regex マッチング化し、`\b` 境界付きパターン運用に変更。無効 regex は debug ログ出力して skip |
| 9 | AC-092〜AC-096 | 設定側 regex の妥当性未検証 | `ac_config_loader.py` で `command_patterns` を `re.compile` 検証し、無効パターンを `skipped_rules` に収集 |
| 10 | — | tool_input 解析ロジックが ac_rule_engine に混在していた | `tool_input_parser.py` に parser を分離し、`hook_event.py` をファサード化、`ac_rule_engine.py` を委譲形式に変更 |
| 11 | AC-008a/008b, AC-140〜AC-147 | read 系の探索スコープと具体パスが同一 `path_patterns` に混在し、deny/confirm の意味論が曖昧 | `scope_patterns` を設定・ローダ・ルール評価へ追加し、`OperationType` / `OverlapKind` で型を明示。read 評価では `concrete_paths` と `scope_patterns` を分離し、包含は deny、不確実交差は confirm、空スコープは confirm 既定、未設定時は `path_patterns` へ後方互換フォールバックするよう修正 |
