---
description: "Use when running, maintaining, or extending hook script test suites in TestHooks/. Trigger phrases: run hook tests, hook test, test hook scripts, add hook test, update run_tests, hooks test suite"
name: "hooks-test"
argument-hint: "run | add <script_name> | update"
agent: "agent"
tools: [read_file, create_file, replace_string_in_file, run_in_terminal, grep_search, file_search]
---

# Hook Script Test Suite

You are maintaining and running unit tests for `.github/hooks/scripts/` in this workspace.

## Directory Layout

```
c:\GHC\
  .github\hooks\scripts\   ← production scripts (SCRIPTS_DIR)
  TestHooks\
    run_tests.ps1           ← master test runner
    <script_name>\
      testcase.md           ← test case spec
      test_<script_name>.py ← unittest file
      testresult.md         ← last run result
```

## run_tests.ps1 Command Reference

### Run all suites
```powershell
powershell -ExecutionPolicy Bypass -File "c:\GHC\TestHooks\run_tests.ps1"
```

### Run a single suite manually
```powershell
Set-Location "c:\GHC\TestHooks\<script_name>"
python -m unittest test_<script_name> -v
```

### Exit codes
| Code | Meaning |
|------|---------|
| 0    | All suites PASS |
| 1    | One or more suites FAIL |

### Output format
- Per-suite detail is printed **only on FAIL**
- Summary table always printed at the end:
  ```
  Script                   Tests Status
  ------                   ----- ------
  workspace_utils             16 PASS
  ...
  Result: 108 / 108 PASS
  ```

## Registered Test Suites

`run_tests.ps1` currently registers these suites (in order):

1. `workspace_utils`
2. `tool_input`
3. `hook_output`
4. `hook_payload`
5. `debug_logging`
6. `check_phase_gate`
7. `post_tool_dashboard_sync`
8. `tool_input_spy`

## Task: Run Tests

When asked to **run tests**:
1. Execute `run_tests.ps1` with `powershell -ExecutionPolicy Bypass -File "c:\GHC\TestHooks\run_tests.ps1"`
2. Report the summary table
3. For any FAIL, show the failing test names and error messages

## Task: Add a New Test Suite

When asked to **add tests for `<script_name>`**:

### Step 1 — Create directory and files
```
TestHooks\<script_name>\
  testcase.md
  test_<script_name>.py
```

### Step 2 — testcase.md format
```markdown
# testcase: <script_name>.py

対象スクリプト: `.github/hooks/scripts/<script_name>.py`

---

## テストケース一覧

| テストID | 観点 | 入力 | 期待動作 |
|----------|------|------|----------|
| XX-001   | ...  | ...  | ...      |
```

### Step 3 — test_<script_name>.py conventions
- Framework: `unittest` + `unittest.mock` (stdlib only, no third-party packages)
- `SCRIPTS_DIR` must be hardcoded as an absolute path:
  ```python
  SCRIPTS_DIR = Path(r"c:\GHC\.github\hooks\scripts")
  ```
- Import the target module dynamically:
  ```python
  import importlib.util, sys
  spec = importlib.util.spec_from_file_location(
      "<script_name>", SCRIPTS_DIR / "<script_name>.py"
  )
  mod = importlib.util.load_module_from_spec(spec)  # adjust as needed
  spec.loader.exec_module(mod)
  ```
- Test IDs follow the pattern `XX-NNN` where `XX` is a 2-letter prefix for the script
- Group related tests in `TestCase` subclasses

### Step 4 — Register in run_tests.ps1
Add the new name to the `$scripts` array in `c:\GHC\TestHooks\run_tests.ps1`:
```powershell
$scripts = @(
    ...existing entries...
    "<script_name>"   # ← append here
)
```

### Step 5 — Run and verify
Run `run_tests.ps1` and confirm the new suite shows PASS.

## Task: Update run_tests.ps1

When asked to **update run_tests.ps1** (e.g., add/remove a suite, change output format):
1. Read the current file: [TestHooks/run_tests.ps1](../../TestHooks/run_tests.ps1)
2. Apply the minimal change requested
3. Re-run to verify exit code 0

## Constraints

- Do NOT install third-party Python packages; use stdlib only
- `SCRIPTS_DIR` must always be the hardcoded absolute path `Path(r"c:\GHC\.github\hooks\scripts")`
- Never change production scripts under `.github/hooks/scripts/` as part of test work
- testresult.md is updated manually or on explicit request — do not auto-update it
