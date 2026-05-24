# testcase: access_control hook

対象スクリプト: `.github/hooks/scripts/entrypoints/access_control.py`
関連モジュール: `ac_config_loader.py`, `ac_rule_engine.py`
設定ファイル: `.github/hooks/config/access-control.json`

---

## テストケース一覧

### ac_config_loader.py

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| AC-001 | `load_config` 正常読み込み | 有効な access-control.json | `AccessControlConfig` を返す。write_rules / read_rules / command_rules が正しく格納される |
| AC-001b | `load_config` 配列形式 backward compat | `write_rules` が配列形式 | `RuleGroup(enabled=True, rules=[...])` として読み込まれる |

### `AccessControlConfig.get_group()`

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| AC-070 | `get_group("write")` | write_rules にルールあり | `write_rules` の RuleGroup を返す |
| AC-071 | `get_group("read")` | read_rules にルールあり | `read_rules` の RuleGroup を返す |
| AC-072 | `get_group("command")` | command_rules にルールあり | `command_rules` の RuleGroup を返す |
| AC-073 | `get_group` 未知タイプ | `operation_type="network"` | 空の `RuleGroup()` を返す |
| AC-002 | `load_config` 不正 action のルールをスキップ＋警告収集 | action が "unknown" のルール + 有効ルール混在 | 不正ルールのみスキップされ、有効ルールが残る。`skipped_rules` にルールID を含むエラーメッセージが1件格納される |
| AC-003 | `load_config` ファイル不在 | 存在しないパス | `FileNotFoundError` が送出される |
| AC-003b | `load_config` JSON 構文エラー | 不正 JSON ファイル | `json.JSONDecodeError` が送出される（`access_control.py` 側で `warn` 送信に変換される） |
| AC-004 | `load_config` ルール空配列 | 各 rules が `[]` | 空リストの `AccessControlConfig` を返す |
| AC-005 | `load_config` disabled action | action="disabled" のルール | `Rule.is_active()` が `False` を返す |
| AC-006 | `_parse_when` path_patterns のみ | `{"path_patterns": ["docs/**"]}` | `WhenClause.path_patterns` に格納される |
| AC-007 | `_parse_when` command_patterns のみ | `{"command_patterns": ["rm -rf"]}` | `WhenClause.command_patterns` に格納される |

### ac_rule_engine.py — evaluate()

#### write 操作

| テストID | 観点 | tool_name | tool_input | rules | 期待動作 |
|----------|------|-----------|------------|-------|----------|
| AC-010 | ルールなし→allow | `create_file` | `{"filePath": "src/main.py"}` | write_rules=[] | `None` を返す |
| AC-011 | パスマッチ→deny | `create_file` | `{"filePath": ".github/hooks/scripts/foo.py"}` | deny ルール `.github/hooks/scripts/**` | deny の `RuleMatch` を返す |
| AC-012 | パスマッチ→confirm | `create_file` | `{"filePath": "docs/basic-design/01-validation.md"}` | confirm ルール `docs/**` | confirm の `RuleMatch` を返す |
| AC-013 | パス不一致→allow | `create_file` | `{"filePath": "src/main.py"}` | deny ルール `docs/**` | `None` を返す |
| AC-014 | disabled→allow | `create_file` | `{"filePath": "docs/foo.md"}` | disabled ルール `docs/**` | `None` を返す |
| AC-015 | deny > confirm 優先 | `create_file` | `{"filePath": "docs/foo.md"}` | confirm ルール + deny ルール、両方 `docs/**` | deny の `RuleMatch` を返す |
| AC-016 | `replace_string_in_file` パスマッチ | `replace_string_in_file` | `{"filePath": ".github/hooks/config/foo.json"}` | deny ルール `.github/hooks/config/**` | deny を返す |
| AC-017 | `multi_replace_string_in_file` 複数パス | `multi_replace_string_in_file` | replacements に `docs/a.md` と `src/b.py` | deny ルール `docs/**` | deny を返す（docs/a.md がマッチ） |

#### read 操作

| テストID | 観点 | tool_name | tool_input | rules | 期待動作 |
|----------|------|-----------|------------|-------|----------|
| AC-020 | ルールなし→allow | `read_file` | `{"filePath": "README.md"}` | read_rules=[] | `None` を返す |
| AC-021 | .env ファイル→deny | `read_file` | `{"filePath": ".env"}` | deny ルール `**/.env` | deny を返す |
| AC-022 | list_dir パスマッチ | `list_dir` | `{"path": "docs/secrets"}` | deny ルール `docs/secrets/**` → 不一致 | `None` を返す（list_dir はディレクトリパス） |
| AC-023 | path_patterns 未指定→全マッチ | `read_file` | `{"filePath": "any/file.txt"}` | deny ルール、when.path_patterns=[] | deny を返す |

#### command 操作

| テストID | 観点 | tool_name | tool_input | rules | 期待動作 |
|----------|------|-----------|------------|-------|----------|
| AC-030 | ルールなし→allow | `run_in_terminal` | `{"command": "ls"}` | command_rules=[] | `None` を返す |
| AC-031 | 破壊的コマンド→deny | `run_in_terminal` | `{"command": "rm -rf ./dist"}` | deny ルール `["rm -rf"]` | deny を返す |
| AC-032 | 大小文字無視マッチ | `run_in_terminal` | `{"command": "RM -RF ./dist"}` | deny ルール `["rm -rf"]` | deny を返す |
| AC-033 | コマンド不一致→allow | `run_in_terminal` | `{"command": "git status"}` | deny ルール `["rm -rf"]` | `None` を返す |
| AC-034 | 強制Git操作→deny | `run_in_terminal` | `{"command": "git push --force origin main"}` | deny ルール `["git push --force"]` | deny を返す |
| AC-035 | command_patterns 未指定→全マッチ | `run_in_terminal` | `{"command": "any command"}` | deny ルール、when.command_patterns=[] | deny を返す |
| AC-036 | 危険コマンド取り込み（settings false由来） | `run_in_terminal` | `{"command": "curl https://example.com"}` など | deny ルール `curl` / `Invoke-WebRequest` / `taskkill` / `chmod` / `Invoke-Expression` 等 | deny を返す |
| AC-037 | 危険オプション取り込み（settings false regex由来） | `run_in_terminal` | `{"command": "date --set 2026-01-01"}` など | deny ルール `date --set` / `find -delete` / `rg --pre` / `sed --expression` / `sort -o` / `tree -o` 等 | deny を返す |
| AC-038 | パッケージインストール→deny | `run_in_terminal` | `{"command": "pip install requests"}` など | deny ルール `pip install` / `pip3 install` / `conda install` / `poetry add` / `pipenv install` / `pipx install` | deny を返す |
| AC-039 | git clone / git push（全般）→deny | `run_in_terminal` | `{"command": "git push origin main"}` / `{"command": "git clone https://..."}` | deny ルール `git push ` / `git clone` | deny を返す |
| AC-042 | PowerShell/Linux系インストール→deny | `run_in_terminal` | `{"command": "Install-Module Pester"}` / `{"command": "apt install git"}` など | deny ルール `Install-Module` / `Install-Package` / `winget install` / `choco install` / `scoop install` / `apt install` / `apt-get install` / `yum install` / `dnf install` / `pacman -S` / `zypper install` / `apk add` / `brew install` / `snap install` / `npm install` / `yarn add` / `pnpm add` | deny を返す |

#### 操作タイプ非対応ツール

| テストID | 観点 | tool_name | 期待動作 |
|----------|------|-----------|----------|
| AC-040 | 未分類ツール→allow | `semantic_search` | `None` を返す |
| AC-041 | 未分類ツール→allow | `grep_search` | `None` を返す |

### パス正規化

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| AC-050 | Windows絶対パス→相対POSIX | `C:\GHC\docs\foo.md`, cwd=`C:\GHC` | `docs/foo.md` として `docs/**` にマッチ |
| AC-051 | cwd外絶対パス→そのままPOSIX | `D:\other\foo.md`, cwd=`C:\GHC` | 相対化されず、`docs/**` にマッチしない |

### 有効/無効制御

| テストID | 観点 | 設定 | tool_name / tool_input | 期待動作 |
|----------|------|------|------------------------|----------|
| AC-008 | グローバル enabled=False | `AccessControlConfig.enabled=False` + deny ルール | `create_file` → `docs/foo.md` | `None` を返す（全ルール無効） |
| AC-060 | write_rules グループ無効 | `write_rules.enabled=False` + deny ルール | `create_file` → `docs/foo.md` | `None` を返す |
| AC-061 | read_rules グループ無効 | `read_rules.enabled=False` + deny ルール | `read_file` → `.env` | `None` を返す |
| AC-062 | command_rules グループ無効 | `command_rules.enabled=False` + deny ルール | `run_in_terminal` → `rm -rf ./dist` | `None` を返す |

### access_control.py — ヘルパー関数

#### `_build_config_warning(config)`

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| AC-080 | skipped_rules 空 → 空文字 | `config.skipped_rules = []` | `""` を返す |
| AC-081 | skipped_rules あり → warning 文字列 | `config.skipped_rules = ["bad-rule: invalid action"]` | `"⚠"` で始まる非空文字列を返す |

#### `_load_config_or_exit(event, config_path)`

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| AC-082 | 設定ファイル不在 | `load_config` が `FileNotFoundError` を送出 | `event.warn()` を呼び出して `sys.exit(0)` |
| AC-083 | 設定ファイル parse エラー | `load_config` が `Exception` を送出 | `event.warn()` を呼び出して `sys.exit(0)` |
| AC-084 | 正常読み込み | 有効な設定ファイル | `config` オブジェクトを返す（sys.exit なし） |

#### `_dispatch_action(event, result, config_warning)`

| テストID | 観点 | result | config_warning | 期待動作 |
|----------|------|--------|----------------|----------|
| AC-085 | result=None + warning なし → 何もしない | `None` | `""` | sys.exit されない。event のメソッド呼ばれない |
| AC-086 | result=None + warning あり → warn 発火 | `None` | `"⚠ bad rules"` | `event.warn()` 呼び出して `sys.exit(0)` |
| AC-087 | action="deny" → deny 発火 | deny の `RuleMatch` | `""` | `event.deny(reason)` 呼び出して `sys.exit(2)` |
| AC-088 | action="deny" + warning あり → warning を reason に付加 | deny の `RuleMatch` | `"⚠ bad rules"` | `event.deny()` の引数に warning が含まれる |
| AC-089 | action="confirm" → ask 発火 | confirm の `RuleMatch` | `""` | `event.ask(reason)` 呼び出して `sys.exit(0)` |
| AC-090 | action="allow" + warning なし → 何もしない | allow の `RuleMatch` | `""` | sys.exit されない。event のメソッド呼ばれない |
| AC-091 | action="allow" + warning あり → warn 発火（リグレッション） | allow の `RuleMatch` | `"⚠ bad rules"` | `event.warn()` 呼び出して `sys.exit(0)`（旧バグ: 握りつぶしていた） |

### コマンドパターン — 正規表現マッチング

#### ac_rule_engine.py — _match_command_patterns(patterns, command, debug)

| テストID | 観点 | patterns | command | 期待動作 |
|----------|------|----------|---------|----------|
| AC-092 | git add が dd false positive を回避 | `["\\bdd\\b", "\\brm\\b"]` | `"git add file.txt"` | `[]` を返す（どのパターンにもマッチしない） |
| AC-093 | dd 単語が \b で厳密マッチ | `["\\bdd\\b"]` | `"dd if=/dev/zero"` | `["\\bdd\\b"]` を返す |
| AC-093b | deadline が \b で非マッチ | `["\\bdd\\b"]` | `"deadline-2026-01-01"` | `[]` を返す |
| AC-094 | 無効な regex パターンが debug ログに記録される | `["\\bdd\\b", "[invalid(regex"]` | `"rm -rf"` | マッチ結果に `[invalid(regex` は含まれず（skip）、debug.log に regex error が記録される |
| AC-095 | 複数の有効パターンor マッチ | `["\\brm\\b", "\\bdd\\b", "dev-null"]` | `"rm -rf ./dist"` | `["\\brm\\b"]` を返す（複数マッチは全て返す） |
| AC-096 | 大小文字無視マッチ | `["\\bDD\\b"]` | `"dd if=/dev/zero"` | `["\\bDD\\b"]` を返す（IGNORECASE で小文字dd がマッチ） |

### tool_input_parser.py — get_write_paths()

| テストID | 観点 | tool_name | tool_input | 期待動作 |
|----------|------|-----------|------------|----------|
| AC-100 | apply_patch: Update File パスを抽出 | `apply_patch` | `{"input": "*** Update File: c:\\GHC\\docs\\foo.md\n@@..."}` | `["c:\\GHC\\docs\\foo.md"]` を返す |
| AC-101 | apply_patch: Add/Delete/Update 複数行 | `apply_patch` | input に Update + Add 2行 | 両パスをリストで返す |
| AC-102 | apply_patch: rename パッチのソースパスのみ返す | `apply_patch` | `{"input": "*** Update File: old.py -> new.py"}` | `["old.py"]` を返す（`-> new.py` は除外） |
| AC-103 | apply_patch: input が文字列でない場合は空を返す | `apply_patch` | `{"input": 42}` | `[]` を返す |
| AC-104 | create_directory: dirPath を返す | `create_directory` | `{"dirPath": "src/subdir"}` | `["src/subdir"]` を返す |
| AC-105 | 非 write ツールは空を返す | `read_file` | `{"filePath": "docs/foo.md"}` | `[]` を返す |

### tool_input_parser.py — get_read_paths()

| テストID | 観点 | tool_name | tool_input | 期待動作 |
|----------|------|-----------|------------|----------|
| AC-110 | read_file: filePath を返す | `read_file` | `{"filePath": "docs/foo.md"}` | `["docs/foo.md"]` を返す |
| AC-111 | get_errors: filePaths リストを返す | `get_errors` | `{"filePaths": ["a.py", "b.py"]}` | `["a.py", "b.py"]` を返す |
| AC-112 | grep_search: includePattern を返す | `grep_search` | `{"includePattern": "src/**/*.py"}` | `["src/**/*.py"]` を返す |
| AC-113 | 非 read ツールは空を返す | `apply_patch` | `{"input": "*** Update File: foo.py"}` | `[]` を返す |

### tool_input_parser.py — get_command_string()

| テストID | 観点 | tool_input | 期待動作 |
|----------|------|------------|----------|
| AC-120 | command キー直接参照 | `{"command": "git status"}` | `"git status"` を返す |
| AC-121 | create_and_run_task: task.command + task.args を合成 | `{"task": {"command": "python", "args": ["-m", "pytest"]}}` | `"python -m pytest"` を返す |
| AC-122 | task.args が空の場合はコマンドのみ | `{"task": {"command": "python", "args": []}}` | `"python"` を返す |
| AC-123 | どのキーも存在しない場合は空文字 | `{}` | `""` を返す |

### ac_rule_engine.py — ツール分類・評価経路確認（tool_input_parser 経由）

| テストID | 観点 | tool_name | tool_input | rules | 期待動作 |
|----------|------|-----------|------------|-------|----------|
| AC-130 | apply_patch のパスが deny ルールにマッチ | `apply_patch` | `{"input": "*** Update File: .github/hooks/scripts/foo.py"}` | deny ルール `.github/hooks/scripts/**` | deny を返す |
| AC-131 | create_and_run_task のコマンドが deny ルールにマッチ | `create_and_run_task` | `{"task": {"command": "rm", "args": ["-rf", "./dist"]}}` | deny ルール `\\brm\\b` | deny を返す |
| AC-132 | send_to_terminal が command ツールとして評価される | `send_to_terminal` | `{"command": "git push origin main"}` | deny ルール `\\bgit\\b\\s+push\\b` | deny を返す |
| AC-133 | grep_search が read ツールとして評価される | `grep_search` | `{"includePattern": ".env"}` | deny ルール `**/.env` | deny を返す（`.env` は `**/.env` にマッチ） |
| AC-134 | workspace 外絶対パスが評価対象から漏れないこと | `create_file` | `{"filePath": "D:/other/secret.py"}` | deny ルール `D:/other/**` | deny を返す（_to_posix_relative で相対化されず、forward-slash 変換後にマッチ） |

### Scope Patterns 判定（ac_rule_engine.py — read 系 scope_patterns 導入）

#### WhenClause scope_patterns パース

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| AC-008a | `_parse_when` scope_patterns のみ | `{"scope_patterns": ["**/.env"]}` | `WhenClause.scope_patterns` に格納される |
| AC-008b | `_parse_when` path + scope 両方 | `{"path_patterns": ["docs/**"], "scope_patterns": ["docs/**"]}` | 両フィールドに正しく格納される |

#### Scope patterns マッチング（glob 交差判定）

| テストID | 観点 | tool_name | tool_input | rules (scope_patterns) | 期待動作 |
|----------|------|-----------|------------|------------------------|----------|
| AC-140 | scope 明確包含: request=wider, rule=narrower | `grep_search` | `{"includePattern": "**/*"}` | deny ルール `**/.env` | deny を返す（全体検索は `.env` を必ず含む） |
| AC-141 | scope 明確包含: request=parent, rule=child | `grep_search` | `{"includePattern": ".github/**"}` | deny ルール `.github/hooks/**` | deny を返す（request が rule を包含） |
| AC-142 | scope 不確実交差: request=wider, rule=narrower | `grep_search` | `{"includePattern": "src/**"}` | deny ルール `src/**/*.env` | confirm を返す（request が wider だが確実でない） |
| AC-143 | scope 明確非交差 | `grep_search` | `{"includePattern": "docs/**"}` | deny ルール `**/.env`, confirm ルール `.github/**` | `None` を返す（どちらも non-overlapping） |
| AC-144 | ambiguous_read（空 includePattern） | `grep_search` | `{"includePattern": ""}` | deny ルール `**/.env` (scope_patterns) | confirm を返す（ambiguous 既定値） |
| AC-145 | file_search query = scope 明確包含 | `file_search` | `{"query": "**/*"}` | deny ルール `**/*.secret` | deny を返す（全体検索は `*.secret` を必ず含む） |
| AC-146 | concrete と scope 両マッチ時の優先（concrete 側 deny） | `read_file` | `{"filePath": ".env"}` | deny ルール（path_patterns=`**/.env`, scope_patterns=`**/*.env`） | deny を返す（path_patterns で即マッチ） |
| AC-147 | 後方互換: scope_patterns 未指定時に path_patterns を使用 | `grep_search` | `{"includePattern": ".env"}` | deny ルール、when.scope_patterns 未指定で when.path_patterns=`**/.env` | deny を返す（従来動作の互換） |
