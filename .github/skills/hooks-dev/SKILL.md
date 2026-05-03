---
name: hooks-dev
description: "Use when creating, debugging, updating, or reviewing VS Code GitHub Copilot agent hook scripts (.py) and JSON configuration files. Covers all 8 event types (PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, Stop, SubagentStart, SubagentStop, PreCompact), blocking and approval patterns, exit code semantics, hookSpecificOutput structure, and Python script best practices. Trigger phrases: create hook, write hook, hook script, implement hook, debug hook, hook configuration, hook payload, PreToolUse hook, PostToolUse hook, permissionDecision, exit code 2, hook template, block tool, agent hook, approve tool, deny tool, hooks development, new hook, add hook"
---

# Hooks Development Skill

## When to Use

Use this skill when you need to:
- Create a new hook script (`.py`) and its JSON configuration file
- Debug or fix an existing hook script that is not behaving as expected
- Understand the payload schema for a specific hook event
- Choose the correct blocking/approval pattern (exit code 2, permissionDecision deny, ask, etc.)
- Understand when to use `continue: false` vs `exit(2)` vs `permissionDecision: "deny"`
- Add debug logging to a hook script using `HookDebugLogger`

---

## Key Reference Documents

| Document | Contents |
|---|---|
| [Hooks-instructions.md](../Hooks-instructions.md) | Architecture overview, common fields, exit code table, spy hook |
| [hooks-docs/payload-PreToolUse.md](../hooks-docs/payload-PreToolUse.md) | PreToolUse input/output schema, blocking patterns |
| [hooks-docs/payload-PostToolUse.md](../hooks-docs/payload-PostToolUse.md) | PostToolUse input/output schema, post-processing patterns |
| [hooks-docs/payload-UserPromptSubmit.md](../hooks-docs/payload-UserPromptSubmit.md) | Prompt interception, audit logging |
| [hooks-docs/payload-SessionStart.md](../hooks-docs/payload-SessionStart.md) | Session initialization, context injection |
| [hooks-docs/payload-Stop.md](../hooks-docs/payload-Stop.md) | Session end, post-processing, stop_hook_active guard |
| [hooks-docs/payload-SubagentStart.md](../hooks-docs/payload-SubagentStart.md) | Subagent startup, context injection |
| [hooks-docs/payload-SubagentStop.md](../hooks-docs/payload-SubagentStop.md) | Subagent completion, result validation |
| [hooks-docs/payload-PreCompact.md](../hooks-docs/payload-PreCompact.md) | Pre-compaction state save |
| [hooks-docs/tool-input-schema.md](../hooks-docs/tool-input-schema.md) | All tool_input schemas, read/write classification table |
| [hooks-docs/hook-template.md](../hooks-docs/hook-template.md) | Full checklist, Python template, blocking pattern examples |
| [hooks/scripts/hook_template.py](../hooks/scripts/hook_template.py) | Python hook script template with `HookOutput` usage examples |
| [hooks/scripts/hook_output.py](../hooks/scripts/hook_output.py) | `HookOutput` class — all output control methods |

---

## Hook Architecture Overview

### File Locations

```
.github/hooks/
  <name>.json            ← Hook configuration (which events → which commands)
  scripts/
    <script_name>.py     ← Python hook script
    debug_logging.py     ← Shared debug logger (already present)
```

### JSON Configuration Format (VS Code)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python .github/hooks/scripts/<script>.py",
        "cwd": ".",
        "timeout": 15
      }
    ]
  }
}
```

> **Note**: VS Code hook config does NOT use `version: 1` at the top level. That field belongs to the Copilot CLI/Cloud Agent format.

### Data Flow

```
Event fires → JSON payload → stdin → Python script → stdout JSON → Copilot processes output
                                                    → stderr     → warning/context to model
                                                    → exit code  → 0=success, 2=block, other=warning
```

### Common Input Fields (All Events)

| Field | Type | Description |
|---|---|---|
| `timestamp` | `string` | ISO 8601 format (NOT Unix milliseconds) |
| `cwd` | `string` | Working directory absolute path |
| `sessionId` | `string` | Session identifier |
| `hookEventName` | `string` | Event name (e.g., `"PreToolUse"`) |
| `transcript_path` | `string` | Path to transcript file |

---

## Output Control Patterns

### Exit Code Semantics

| Exit Code | Behavior |
|---|---|
| `0` | Success — parse stdout as JSON |
| `2` | **Block** — stop tool/action, show stderr to model as error context |
| Other non-zero | Non-blocking warning — continue processing, stderr shown as warning |

### Output Method Selection Guide

| Goal | Method |
|---|---|
| Continue normally (no block, no warning) | Return from `main()` without calling anything — output nothing |
| Block a single tool call (simplest) | `sys.exit(OUT.block("message"))` |
| Block with user-visible reason | `sys.exit(OUT.deny("reason"))` |
| Request user confirmation | `sys.exit(OUT.ask("reason"))` (VS Code only) |
| Modify tool inputs before execution | `sys.exit(OUT.update_input(new_input_dict))` |
| Add context to conversation | `sys.exit(OUT.add_context("text"))` |
| Show a warning without blocking | `sys.exit(OUT.warn("message"))` |
| Stop the entire session | `sys.exit(OUT.stop_session("reason"))` |
| PostToolUse block | `sys.exit(OUT.block_post("reason"))` |
| Stop event: prevent session ending | `sys.exit(OUT.block_stop("reason"))` |

> **Critical distinction**: `stop_session()` stops the **entire session**. Do NOT use it to block a single tool call — use `deny()` or `block()` instead.
>
> **stdout discipline**: Only call `OUT.method()` when you have something to communicate. Return from `main()` silently when no action is needed.

### hookSpecificOutput Structure by Event

| Event | Output Structure |
|---|---|
| `PreToolUse` | `hookSpecificOutput.permissionDecision` / `permissionDecisionReason` / `updatedInput` / `additionalContext` |
| `PostToolUse` | Top-level `decision:"block"` + `reason` + `hookSpecificOutput.additionalContext` |
| `SessionStart` | `hookSpecificOutput.additionalContext` |
| `Stop` | `hookSpecificOutput.decision:"block"` + `hookSpecificOutput.reason` (WITH wrapper) |
| `SubagentStart` | `hookSpecificOutput.additionalContext` |
| `SubagentStop` | Top-level `decision:"block"` + `reason` (NO wrapper — different from Stop!) |
| `UserPromptSubmit` | Common fields only (no hookSpecificOutput) |
| `PreCompact` | Common fields only (no hookSpecificOutput) |

---

## Implementation Procedure

1. **Identify the event** — which of the 8 events best fits the use case?
2. **Read the payload spec** — open the corresponding `hooks-docs/payload-<Event>.md`
3. **Copy the Python template** — from `hooks-docs/hook-template.md`
4. **Implement logic** — use `_read_input()`, check required fields, implement the hook behavior
5. **Add debug logging** — `DEBUG.log("input", ...)` at entry, `DEBUG.log("done", ...)` at exit
6. **Choose output pattern** — from the Output Control Patterns table above
7. **Create/update JSON config** — add event to `.github/hooks/<name>.json`
8. **Test with spy hook** — enable `tool-spy.json` to observe raw payloads (see Hooks-instructions.md §5)
9. **Enable debug logging** — create `<script_name>.debug` file to activate `HookDebugLogger` output
10. **Verify exit codes** — test that exit 2 correctly blocks, exit 0 continues

---

## Debugging Guide

### Enable Debug Mode

Create the debug flag file (same directory as the script, no extension content required):

```powershell
# Windows
New-Item -ItemType File ".github/hooks/scripts/<script_name>.debug"
```

Logs will be written to `.github/hooks/scripts/<script_name>.debug.log`.

### Read Hook Output in VS Code

Hook output (stdout/stderr) appears in the **GitHub Copilot Chat** output channel. Open:
`View > Output > GitHub Copilot Chat (Hooks)` or similar.

### Use the Spy Hook

The `tool-spy.json` hook logs all PreToolUse and PostToolUse payloads to a JSONL file.
See [Hooks-instructions.md §5](../Hooks-instructions.md#5-スパイフックの使い方) for usage.

### Test a Script Manually

```powershell
# Pipe test payload to the script
echo '{"hookEventName":"PreToolUse","tool_name":"run_in_terminal","tool_input":{"command":"rm -rf /"},"cwd":".","sessionId":"test","timestamp":"2026-01-01T00:00:00.000Z","transcript_path":"/tmp/t.jsonl","tool_use_id":"test-001"}' | python .github/hooks/scripts/<script_name>.py
```

---

## Common Pitfalls

| Pitfall | Correct Approach |
|---|---|
| Using `continue: false` to block a single tool | Use `permissionDecision: "deny"` or `sys.exit(2)` |
| Not checking `stop_hook_active` in `Stop`/`SubagentStop` | Always check — infinite loop if you block every time |
| Treating `read_file` as a write tool (it has `filePath` too) | Filter by `tool_name` first, then check `filePath` |
| `timestamp` as integer (Unix ms) | In VS Code, `timestamp` is ISO 8601 string |
| `permissionDecision: "ask"` not showing dialog | This works in VS Code only, not in Cloud Agent/CLI |
| Missing `hookSpecificOutput` wrapper in PreToolUse output | Wrap in `hookSpecificOutput: { hookEventName: "PreToolUse", ... }` |
| `SubagentStop` using `hookSpecificOutput.decision` | SubagentStop uses **top-level** `decision` (no wrapper) |
| Stop hook using top-level `decision` | `Stop` uses `hookSpecificOutput.decision` (WITH wrapper) |
| Non-zero exit code other than 2 causes block | Only exit code `2` blocks; other non-zero = warning only |
| JSON output with `ensure_ascii=True` (default) | Always use `ensure_ascii=False` for Japanese characters |
