---
name: severity-triage
description: "Use when classifying verification findings from adversarial checks into severity levels Lv1/Lv2/Lv3. Determines the required response: auto-fix (Lv1), draft proposal awaiting approval (Lv2), or human decision required for tradeoffs (Lv3). Trigger phrases: severity classification, triage findings, Lv判定, 重大度分類, classify finding, finding classification"
---

# Severity Triage Skill

## Purpose

Classify each verification finding (from `perspective-checker` subagents or V1 static checks) into one of three severity levels that determine the required response.

## Severity Levels Summary

| Level | Definition | Required Action |
|-------|------------|-----------------|
| **Lv1** | Objective, rule-based, automatically verifiable and fixable | Auto-fix + brief log entry |
| **Lv2** | Design/policy-related; a correct answer exists but human confirmation is preferred | Draft fix proposal + await approval in Stage 5 |
| **Lv3** | Tradeoff/strategic judgment; no single correct answer | Present decision options + block Stage 5 until resolved |

---

## Lv1 Identification Criteria

A finding is **Lv1** if ALL of the following are true:
1. The violation is objectively verifiable — no interpretation required to identify it
2. The correct fixed state can be determined by a rule lookup or mechanical comparison
3. The fix can be applied without design judgment or team policy decisions

**Lv1 examples** (any of these qualifies as Lv1):
- YAML frontmatter `---` block is not closed
- `name` value does not match the filename (without extension) or parent folder name
- A required field (`name` or `description`) is absent
- `description` contains a bare colon `:` without surrounding quotes
- Vague/weak language used inside a DO NOT / ONLY / MUST rule:「適切に」「必要に応じて」「考慮する」「望ましい」
- Explicitly prohibited Python package is imported (`import requests`, `import numpy`, `import pandas`, etc.)
- Explicitly prohibited PowerShell module is used (called via `Install-Module`)
- An exact duplicate rule already exists verbatim in an existing committed file
- `tools` field value is not an array (e.g., written as a string instead of `[...]`)

---

## Lv3 Identification Criteria

A finding is **Lv3** if ANY of the following are true:
- Multiple reasonable alternatives exist and the correct choice depends on team or org policy
- The finding is about rule granularity (how strict/broad to make a constraint)
- Applying the obvious fix would create a new tradeoff (gain in one area, loss in another)
- The finding involves balancing agent autonomy vs. human oversight
- Reasonable people could disagree in good faith about whether it is actually a problem
- The scope of impact is large (e.g., change to `copilot-instructions.md` affecting all agents)
- The finding requires domain-specific or project-specific context to resolve

**Lv3 examples**:
- Should a rule be placed in `copilot-instructions.md` (global) vs. a specific skill (scoped)?
- Should the scope of a constraint be X only, or X + Y?
- Is the level of prescriptiveness appropriate for this team's workflow?
- A policy conflict between two files requires deciding which takes precedence
- Adding more restrictions will reduce agent flexibility — is that acceptable?
- Rule coverage is too narrow (may need expanding) but expanding has side effects

---

## Lv2 Identification Criteria

A finding is **Lv2** if it is **not Lv1 and not Lv3**:
- A logical issue exists and a correct fix can be proposed, but AI-generated fixes need human sign-off
- A required section is missing from a skill or agent file (what to write requires some design judgment)
- A statement is logically contradictory with an existing rule (the fix is clear, but the change is not trivial)
- An effectiveness gap: a rule states a goal but not a concrete action
- A structural anti-pattern is detected (e.g., swiss-army tools), but the specific fix requires discussion

**Lv2 examples**:
- A required section (`## Role Constraints`, output format, etc.) is missing from an agent file
- A rule fails the "does it change agent behavior?" test — too abstract to act on
- A finding about missing alternative actions in a prohibition-only rule
- Swiss-army tool pattern detected, but which specific tools to remove is debatable

---

## Classification Procedure

For each finding received from a `perspective-checker` subagent or V1 static check:

1. **Lv1 test**: Check all Lv1 criteria. If ALL conditions are met → assign **Lv1**.
2. **Lv3 test**: Check all Lv3 criteria. If ANY condition is met → assign **Lv3**.
3. **Default**: If neither Lv1 nor Lv3 → assign **Lv2**.

**Escalation principle**: When uncertain between Lv2 and Lv3, prefer **Lv3**.  
It is safer to escalate a finding to human judgment than to auto-propose a fix for a strategic decision.

---

## Output Format Per Finding

```
[LvN] {観点ID} — {指摘の要約（1行、20字以内推奨）}
詳細  : {指摘の詳細説明。なぜ問題か、草案のどの箇所が該当するか。}
根拠  : {なぜこの Lv になったか、1〜2文で Lv 判定根拠を明示}
対応  :
  Lv1 → 修正内容: {Before} → {After}
  Lv2 → 修正素案: {具体的な修正案テキスト}
  Lv3 → 選択肢A: {内容} / 選択肢B: {内容} / 判断軸: {何を重視するかで決まるか}
```

---

## Aggregation Output

After classifying all findings, produce a summary:

```
### Lv 集計サマリー

| Level | 件数 | 状態 |
|-------|------|------|
| Lv1   | N    | ✅ 自動修正済み |
| Lv2   | N    | ⚠ 承認待ち |
| Lv3   | N    | ⛔ 人間判断必須 |

### ゲート判定
```

Gate judgment rules:
- Lv3 が 1件以上 → `⛔ 人間判断必須 — Stage 5 進行前に Lv3 を全て解決すること`
- Lv3 が 0件 かつ Lv2 が 1件以上 → `⚠ Lv2 承認待ち — Stage 5 の承認ダイアログで確認`
- Lv1 のみ または 指摘なし → `✅ 自動修正完了 — Stage 5 へ進行可能`
