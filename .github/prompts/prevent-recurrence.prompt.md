---
description: "Use when the user reports a mistake, process violation, or recurring issue by the agent: run a full post-incident review covering investigation, complaint validation, trade-off analysis, prevention proposal, implementation, and effectiveness verification. Trigger phrases: prevent recurrence, post-incident, fix recurring mistake, agent error, why did this happen, 再発防止, 振り返り, 指摘対応, なぜこうなった"
name: prevent-recurrence
argument-hint: "<ユーザーからの指摘内容を貼り付ける>"
agent: "prevent-recurrence"
---

You are performing a structured post-incident review for the following user complaint:

$input

## Instructions

Execute all stages defined in your agent instructions in order without skipping.

### Stage sequencing rules

1. Complete Stages 1–5 as a written report first.
2. **Stop at Stage 5** and use `vscode/askQuestions` to present an approval dialog to the user before proceeding.
   - Options: ✅ Approve / ❌ Reject / 🔄 Revise
   - If **Approved**: proceed to Stage 6.
   - If **Rejected**: stop and report cancellation.
   - If **Revise**: return to Stage 4, incorporate the feedback, and re-present Stage 5.
3. Only after approval: execute Stage 6 (implementation), then Stage 7 (verification).
4. After Stage 7: Execute Stage 8.
   - Classify artifacts: test files (`test_*.py`, `testcase.md`, `testresult.md`) → delegate to `test-fix`;
     other artifacts (`docs/`, `src/`) → delegate to `artifact-fix`.
   - Pass ONLY: target file paths + Stage 1–2 factual findings. Do NOT include fix policies —
     each subagent designs its own fix approach autonomously.
   - `test-fix` is responsible for asking the user about test execution and running tests if approved.
     Do NOT handle test execution in this agent.
   - Skip Stage 8 and report completion if no artifacts need fixing.
5. If your agent instructions define artifact verification branches after Stage 8, execute them in order and then produce the final report.

### Scope constraints

- Investigations are limited to recent git history and `.github/` files.
- This agent's direct edits are limited to `.github/` customization files only:
  `copilot-instructions.md`, `agents/`, `skills/`, `prompts/`, `instructions/`
- Artifact fixes (docs/, src/, etc.) are delegated to the `artifact-fix` subagent in Stage 8. This agent must not directly edit those files.

### Output quality rules

- Stage 1: state only confirmed facts — no speculation.
- Stage 2: cite the exact rule text that was violated or followed.
- Stage 3: always include at least one "do nothing" option in the trade-off table.
- Stage 4: draft the exact text change (diff style) for each candidate.
- Stage 5: present the diff clearly and ask for approval with explicit options.
- Stage 6: read each file before editing; use `todo` to track each change item.
- Stage 7: trace the prevention logic step-by-step to confirm it covers the reported incident.
- Stage 7: self-verify all changed files and report per-file PASS/FAIL.
- Stage 7 self-verification fields: file path, check point, evidence, decision reason.
- If any file is FAIL in Stage 7, return to Stage 4 and revise before proceeding.
