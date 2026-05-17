---
description: "Use when verifying runtime behavior of hook policies end-to-end: workspace file create/read, safe command run, confirm/ask checks, deny enforcement, and payload compatibility. Includes pre/post handling (stash, cleanup) and test/** verification branch workflow. Trigger phrases: verify hooks runtime, hook e2e check, deny confirm ask test, runtime hook validation, フック実動作確認"
name: verify-hooks-runtime
argument-hint: "smoke | full | rule:<rule_id>"
agent: agent
---

# Verify Hooks Runtime

You validate hook runtime behavior in this workspace with a reproducible operational flow.

## Scope

This command verifies all of the following in one run:
- A: workspace file create/read path works as expected
- B: one harmless terminal command runs as expected
- C: protected-path write triggers confirm/ask behavior
- D: deny rule blocks matching command and returns a rule id
- E: payload compatibility assumptions remain valid (snake_case/camelCase handling)

## Required Safety and Workflow

Always execute in this order.

1. Pre-check and save state
- Record current branch name.
- Save current worktree changes with stash.
- If stash fails, stop and report.

2. Cleanup verification artifacts
- Remove stale probe files under:
  - tmp/workspace-probe/
  - .github/hooks/config/probe*
- Do not delete source files.

3. Create verification branch
- Create and switch to a branch named:
  - test/verify-hooks-<YYYYMMDD-HHMMSS>
- Never delete this verification branch automatically.

4. Run runtime verification
- For A and B, invoke workspace-probe subagent with safe inputs.
- For C, attempt write under .github/hooks/config/ and capture whether confirm/ask is returned.
- For D, run a harmless command string that intentionally matches a deny rule and confirm block message + rule id.
- For E, inspect recent hook logs and payload parsing assumptions for snake_case/camelCase key handling.

5. Post-processing
- Switch back to the original branch.
- Restore stash automatically.
- If stash restore conflicts, stop immediately and report exact recovery steps.

## Modes

- smoke:
  - Run A and D only.
- full:
  - Run A, B, C, D, E.
- rule:<rule_id>:
  - Run D for a specific deny rule id and include exact evidence.

## Output Format

Return the report with these sections in plain markdown:

### Runtime Verification Summary
- Mode: <smoke|full|rule:*>
- Original Branch: <name>
- Verification Branch: <name>
- Stash: <created/restored/conflict>

### Check Results
- A create/read: PASS | FAIL
- B safe command: PASS | FAIL | SKIPPED
- C confirm/ask: PASS | FAIL | SKIPPED
- D deny enforcement: PASS | FAIL
- E payload compatibility: PASS | FAIL | SKIPPED

### Evidence
- Include concrete tool outputs for each non-skipped check.
- For D, include the deny message and matched rule id.

### Notes
- Include cleanup actions performed.
- Mention any manual recovery needed.

## Constraints

- Do not run destructive commands.
- Do not install packages.
- Do not run full unit tests unless user explicitly asks.
- Keep operations inside workspace.
- If any critical step fails (stash create, branch switch, stash restore), stop and report immediately.
