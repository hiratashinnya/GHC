---
description: "Use when the user reports a mistake, process violation, or recurring issue by the agent: run a full post-incident review covering investigation, complaint validation, trade-off analysis, prevention proposal, implementation, and effectiveness verification. Trigger phrases: prevent recurrence, post-incident, fix recurring mistake, agent error, why did this happen, 再発防止, 振り返り, 指摘対応, なぜこうなった"
name: prevent-recurrence
argument-hint: "<ユーザーからの指摘内容を貼り付ける>"
agent: "prevent-recurrence"
---

You are performing a structured post-incident review for the following user complaint:

$input

## Instructions

Execute all 7 stages defined in your agent instructions **in order without skipping**.

### Stage sequencing rules

1. Complete Stages 1–5 as a written report first.
2. **Stop at Stage 5** and use `vscode/askQuestions` to present an approval dialog to the user before proceeding.
   - Options: ✅ Approve / ❌ Reject / 🔄 Revise
   - If **Approved**: proceed to Stage 6.
   - If **Rejected**: stop and report cancellation.
   - If **Revise**: return to Stage 4, incorporate the feedback, and re-present Stage 5.
3. Only after approval: execute Stage 6 (implementation), then Stage 7 (verification).

### Scope constraints

- Investigations are limited to recent git history and `.github/` files.
- Edits are limited to `.github/` customization files only:
  `copilot-instructions.md`, `agents/`, `skills/`, `prompts/`, `instructions/`
- Do **not** modify production code, test files, or docs.

### Output quality rules

- Stage 1: state only confirmed facts — no speculation.
- Stage 2: cite the exact rule text that was violated or followed.
- Stage 3: always include at least one "do nothing" option in the trade-off table.
- Stage 4: draft the exact text change (diff style) for each candidate.
- Stage 5: present the diff clearly and ask for approval with explicit options.
- Stage 6: read each file before editing; use `todo` to track each change item.
- Stage 7: trace the prevention logic step-by-step to confirm it covers the reported incident.
