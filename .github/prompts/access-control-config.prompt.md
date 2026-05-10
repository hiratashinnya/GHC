---
description: "Use when adding, updating, or reviewing command/path deny rules in access-control.json. Trigger phrases: access control, deny rule, allow rule, command rule, block command, access-control.json, アクセス制御, denyルール, コマンドブロック"
name: "access-control-config"
argument-hint: "add-command <pattern> | add-path <glob> | change-action <rule-id> <action> | import-from-settings | review"
agent: "agent"
tools: [read_file, replace_string_in_file, multi_replace_string_in_file, grep_search, run_in_terminal]
---

# Access Control Config Operations

You are editing `.github/hooks/config/access-control.json` — the PreToolUse hook rule set for this workspace.

## Key Files

| File | Role |
|------|------|
| `.github/hooks/config/access-control.json` | Rule definitions (edit target) |
| `.github/hooks/scripts/ac_rule_engine.py` | Matching engine (read to understand behavior) |
| `.github/hooks/scripts/ac_config_loader.py` | Config loader (read to check supported schema) |
| `TestHooks/access_control/testcase.md` | Test case spec (update BEFORE editing JSON) |
| `TestHooks/access_control/test_access_control.py` | Unit tests (update after testcase.md) |
| `TestHooks/access_control/testresult.md` | Test run record (update after test execution) |

## Matching Behavior (from ac_rule_engine.py)

- **command_patterns**: plain substring match, case-insensitive. NO regex support.
- **path_patterns**: fnmatch glob. `**/foo` matches root-level `foo` too.
- **Priority**: `deny` > `confirm`. First match per priority wins.
- **disabled** action: rule is parsed but never fires.

## Rule Schema

```json
{
  "id": "deny-<category>",
  "description": "<Japanese description>",
  "action": "deny | confirm | disabled",
  "when": {
    "command_patterns": ["<substring>"],
    "path_patterns": ["<glob>"]
  }
}
```

Rule groups: `write_rules`, `read_rules`, `command_rules`. Each has `enabled` flag.

## Workflow by Argument

### `add-command <pattern>`
1. Identify which existing rule id the pattern belongs to (category match).
2. If a matching rule exists, add the pattern to its `command_patterns` array.
3. If no match, create a new rule with a descriptive `id` and `description`.
4. Update `testcase.md` first, then `test_access_control.py`, then commit, then test.

### `add-path <glob>`
1. Determine target group: `write_rules` (file write tools) or `read_rules` (file read tools).
2. Add the glob to the appropriate rule's `path_patterns`.
3. Follow the same test update order as above.

### `change-action <rule-id> <action>`
1. Locate the rule by `id`.
2. Change its `action` field.
3. Update any test that asserts the old action value.

### `import-from-settings`
Source: `chat.tools.terminal.autoApprove` in VS Code `settings.json`.
Steps:
1. Read settings and collect all entries with `false` value.
2. Map each to the appropriate rule category (see Category Map below).
3. Add missing patterns. Skip if already covered by an existing pattern.

### `review`
Check for:
- Patterns too broad (e.g., `"rm "` blocks `"format rm"` output accidentally).
- Missing coverage vs. settings.json false entries.
- Rules with `disabled` that should be active.
- Duplicate patterns across rules.

## Category Map (for import-from-settings)

| Category | Rule ID | Example patterns |
|----------|---------|-----------------|
| 削除系 | `block-destructive-delete` | `rm `, `Remove-Item `, `del ` |
| プロセス停止系 | `deny-process-control-commands` | `kill `, `Stop-Process`, `taskkill` |
| 外部通信系 | `deny-network-fetch-commands` | `curl `, `wget `, `Invoke-WebRequest` |
| 権限変更系 | `deny-permission-and-property-changes` | `chmod `, `Set-Acl` |
| 任意実行系 | `deny-expression-execution` | `eval `, `Invoke-Expression`, `iex ` |
| Git 破壊系 | `deny-git-force-push` / `deny-git-reset-hard` / `deny-git-dangerous-options` | `git push --force`, `git reset --hard` |
| 危険オプション系 | `deny-dangerous-tool-options` | `date --set`, ` -delete`, `sed --expression` |
| ディスク操作系 | `block-disk-format` | `diskpart`, `format ` |

## Mandatory Test Order (repository rule)

> testcase.md（仕様）→ テストコード実装 → コミット → テスト実行 → testresult.md 記録

1. Update `testcase.md` (add/modify test case rows).
2. Update `test_access_control.py` (add/modify test methods).
3. Commit all changed files.
4. Run: `python -m unittest discover -s TestHooks/access_control -p "test_access_control.py" -v`
5. Record result in `testresult.md` with `実行日:` and `コミットID:` (from `git log --oneline -1`).
