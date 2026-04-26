---
name: dashboard-pipeline
description: "Use when rebuilding or synchronizing docs/dashboard.md by running the full D-1→D-2→D-3 pipeline. Also detects unmerged approved diffs in iter/ and generates a next-action recommendation. Trigger phrases: dashboard pipeline, rebuild dashboard, update status matrix, detect bottlenecks, sync dashboard state, refresh dashboard, dashboard pipeline run"
argument-hint: "Optional: specify docs-dir (default: docs) or dashboard path (default: docs/dashboard.md)"
---

# Dashboard Pipeline

Run the full D-1 → D-2 → D-3 automation pipeline to rebuild `docs/dashboard.md` from actual document frontmatter. Then scan `iter/` for unmerged approved diffs and generate a next-action recommendation.

## When to Use

- At session start, to restore project state from file reality
- After any document's `status` field changes
- At phase or process transitions
- When the orchestrator detects a mismatch between dashboard and file state
- Before delegating to a phase subagent
- After `doc-merge` completes (to refresh the matrix)

## Prerequisites

- `docs/` directory exists with at least one phase subdirectory
- `docs/dashboard.md` exists (initialized from `.github/templates/dashboard.md`)
- Python is available in the workspace environment
- Scripts `patch_dashboard.py` and `scan_unmerged_diffs.py` exist under `.github/scripts/`

---

## Procedure

### Step 1: Run D-3 — Patch Dashboard

Execute the dashboard patcher:

```
python .github/scripts/patch_dashboard.py --docs-dir docs --dashboard docs/dashboard.md
```

`patch_dashboard.py` is self-contained — it internally invokes the same logic as D-1 and D-2 via shared `_lib` functions:
- Scans all `docs/{phase}/0[1-5]-*.md` and `docs/detailed-design/components/**/*.md`
- Reads `status` from each file's YAML frontmatter; maps to emoji (see table below)
- Builds status matrix, component progress table, and bottleneck list in one pass
- Replaces the "フェーズ × プロセス ステータスマトリクス" table in `docs/dashboard.md`
- Replaces the "詳細設計 コンポーネント別進捗" table (if detailed-design components exist)
- Replaces the "ボトルネック" section
- Updates the `last-updated` frontmatter field to current datetime (`YYYY-MM-DD HH:MM`)

Output JSON: `{ "success": true, "dashboard": "<path>", "updated_at": "YYYY-MM-DD HH:MM" }`

Confirm `"success": true`. If the script exits with a non-zero code, report the stderr output and stop.

**Status → Emoji Mapping:**

| `status` value      | Symbol |
| --------------------- | -------- |
| `approved`          | ✅     |
| `awaiting-approval` | ⏳     |
| `draft`             | 📝     |
| `rejected`          | ❌     |
| `under-revision`    | 🔙     |
| (file absent)       | `─`    |

---

### Step 2: Read Dashboard

Read `docs/dashboard.md` to obtain the current project state:
- "フェーズ × プロセス ステータスマトリクス" — phase/process status overview
- "詳細設計 コンポーネント別進捗" — component-level progress (detailed-design only)
- "ボトルネック" — list of blocked / rejected / under-revision documents

---

### Step 3: Detect Unmerged Approved Diffs

Execute the unmerged diff scanner:

```
python .github/scripts/scan_unmerged_diffs.py --iter-dir iter --docs-dir docs
```

`scan_unmerged_diffs.py` scans `iter/` recursively and:
- Reads YAML frontmatter from every `iter/**/*.md`
- Selects files where `doc-kind: diff` and `status: approved`
- Cross-references the corresponding master in `docs/<phase>/` by comparing `master.version` vs `diff.base-version`; if `master.version <= base-version` (or master absent), the diff is considered unmerged

Output JSON: `{ "unmerged": [{diff_path, master_path, phase, process, iteration, base_version}, ...], "total": N }`

If `total` is `0`, report "No unmerged approved diffs found."
If the script exits with a non-zero code, report the stderr output and stop.

---

### Step 4: Generate Result Summary (AI)

Compose a structured summary in the following format:

```
📊 Dashboard Pipeline Result [YYYY-MM-DD HH:MM]
───────────────────────────────────────────────
Bottlenecks   : <N> item(s)
  <list each bottleneck path and status — or "none">

Unmerged Diffs: <N> item(s)
  <list each diff path and target master — or "none">

Next Action   : <single recommended action>
───────────────────────────────────────────────
```

**Next Action decision rules (priority order):**

1. If any gate doc (`approval-required: true`) has `status: awaiting-approval` → "Obtain human approval for `<path>`"
2. If any gate doc has `status: rejected` → "Handle rejection for `<path>` — consult routing-on-failure skill"
3. If unmerged approved diffs exist → "Merge approved diff `<path>` into `<master>` — consult doc-merge skill"
4. If the current process has no diff doc in `iter/` yet → "Create diff doc for `<phase>/<process>` in `iter/iterN/phaseX/`"
5. If all processes in current phase are `approved` → "All processes in `<phase>` approved — proceed to next phase"
6. Otherwise → "Continue work on `<phase>` process <N>"
