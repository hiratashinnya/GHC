---
description: "Use when manually running the adversarial verification pipeline against one or more .github/ draft files, outside of the prevent-recurrence workflow. Runs V1 (static check + Lv1 auto-fix) → V2 (multi-perspective independent analysis) → V3 (severity triage + report). Trigger phrases: adversarial check, run adversarial, verify draft, quality check draft, 敵対的検証, 草案検証, 品質検証, Lv判定"
name: run-adversarial
argument-hint: "<検証対象ファイルのパスを1行1ファイルで列挙。省略時は直前の会話コンテキストから推測>"
agent: "adversarial"
---

You are running the adversarial verification pipeline. Analyze the following draft target(s):

$input

## Instructions

Run the full 3-stage adversarial verification pipeline as defined in your agent instructions.

### Parameters

- **draft_targets**: The file path(s) provided above as `$input`. If no paths are given, infer the target from the current conversation context (most recently discussed `.github/` file).
- **stage1_2_summary**: Extract from the current conversation context if available. If no prior incident summary exists, set this to: `"スタンドアロン実行 — 指摘事項なし。形式・構造・観点チェックのみ実施。"`
- **perspective_scope**: Use all perspectives (default):
  - `.github/perspectives/customization.md` (P-CUS-01〜05)
  - `.github/perspectives/prevent-recurrence.md` (P-PR-01〜05) — skip if the draft is NOT a prevent-recurrence proposal

### Stage sequencing

Execute in order — do not skip stages:

1. **Stage V1**: Static formal check. Apply Lv1 auto-fixes immediately. Log all changes.
2. **Stage V2**: For each applicable perspective section, invoke `perspective-checker` as an independent subagent. Pass V1-corrected drafts. Do NOT share results between subagent calls.
3. **Stage V3**: Aggregate all findings. Use `severity-triage` skill for final Lv classification. Generate the full verification report.

### Perspective selection guidance

| Draft type | Perspectives to use |
|------------|---------------------|
| `agents/*.agent.md`, `skills/*/SKILL.md`, `prompts/*.prompt.md`, `instructions/*.md`, `copilot-instructions.md` | `customization.md` (P-CUS-01〜05) **+** `prevent-recurrence.md` (P-PR-01〜05) if it's a prevent-recurrence proposal |
| Any other `.github/` file | `customization.md` (P-CUS-01〜05) only |
| Only perspective checking (no prevent-recurrence context) | `customization.md` (P-CUS-01〜05) only |

### Output requirements

Produce the complete verification report in the format defined in your agent instructions:

```
# 敵対的検証レポート
実施日時: ...
草案対象: ...
使用観点: ...

## V1: 静的検証（自動修正結果）
...

## V2+V3: 多角検証 + トリアージ結果
### Lv 集計サマリー
...
### ゲート判定
...
### Lv3 指摘（ブロック事項）[Lv3 > 0 件の場合]
...
### Lv2 指摘（承認待ち）[Lv2 > 0 件の場合]
...

## 引き渡しサマリー
...
```

### Standalone behavior (no prevent-recurrence context)

When invoked as a standalone command (not from `prevent-recurrence`):
- Report Lv1 auto-fix results.
- For Lv2: present findings and ask the user whether to apply the proposed fix using `vscode/askQuestions`.
- For Lv3: present options A/B and ask the user to decide before any action is taken.
- Do NOT automatically proceed to implementation — wait for explicit user confirmation.
