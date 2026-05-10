# testresult: access_control hook

対象スクリプト: `.github/hooks/scripts/access_control.py`
関連モジュール: `ac_config_loader.py`, `ac_rule_engine.py`
実行日: 2026-05-10
コミットID: 107af03
実行コマンド: `python -m unittest test_access_control -v`
総合結果: **PASS** (52/52)

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
| AC-030 | TestEvaluateCommandRules | command: ルールなし → allow | `None` | PASS |
| AC-031 | TestEvaluateCommandRules | command: `rm -rf` → deny | deny を返す | PASS |
| AC-032 | TestEvaluateCommandRules | command: 大小文字無視マッチ | deny を返す | PASS |
| AC-033 | TestEvaluateCommandRules | command: パターン不一致 → allow | `None` | PASS |
| AC-034 | TestEvaluateCommandRules | command: `git push --force` → deny | deny を返す | PASS |
| AC-036 | TestEvaluateCommandRules | command: settings false 由来の危険パターン → deny（11種サブテスト） | 全サブテスト deny を返す | PASS |
| AC-035 | TestEvaluateCommandRules | command: command_patterns 未指定 → 全マッチ | deny を返す | PASS |
| AC-040 | TestUnknownTools | 未分類ツール `semantic_search` → allow | `None` | PASS |
| AC-041 | TestUnknownTools | 未分類ツール `grep_search` → allow | `None` | PASS |
| AC-050 | TestPathNormalization | Windows絶対パス → 相対化 → `docs/**` マッチ | deny を返す | PASS |
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

---

## 修正記録

| # | テストID | 問題 | 修正内容 |
|---|----------|------|----------|
| 1 | AC-021 | `fnmatch(".env", "**/.env")` が `/` なしで不一致 | `_match_single_path()` を追加し、`**/` プレフィックスのパターンはルート直下ファイルにも適用するよう修正 |
| 2 | AC-001〜007 | `AccessControlConfig` の `write_rules` 等が `List[Rule]` → `RuleGroup` に変更 | テスト全件を `.write_rules.rules[0]` 形式に更新、`_make_config()` を `RuleGroup` を返すよう更新 |
| 3 | AC-004 | `test_AC004` の `def` ヘッダが欠落し AC-003b 内に混入していた | `def test_AC004_empty_rules(self):` ヘッダを独立したメソッドとして復元 |
| 4 | — | `_get_candidate_rules` が `AccessControlConfig` のフィールド名を直接知っていた（凝集度違反） | `AccessControlConfig.get_group()` メソッドを追加し、`_get_candidate_rules` を thin adapter に変更 |
| 5 | AC-036 | `find -delete` パターンが `find . -delete` にサブストリング不一致 | テストパターンを ` -delete` に修正（access-control.json と整合） |
