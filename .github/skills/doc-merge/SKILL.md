---
name: doc-merge
description: "Use when merging approved diff documents from iter/ into docs/ master documents. Handles version increment, frontmatter update, content merge, and post-merge validation. Trigger phrases: merge diff, merge to master, merge document, merge approved, diff to master, merge iter, master merge, document merge"
argument-hint: "Specify the diff document path to merge, e.g. iter/iter1/phase2/02-breakdown.md"
---

# Document Merge (Diff → Master)

Merge an approved diff document from `iter/iterN/phaseX/` into the corresponding master document in `docs/<phase>/`. This skill ensures version consistency, frontmatter correctness, and post-merge integrity.

## When to Use

- A diff document's `status` has been set to `approved`
- The orchestrator determines a diff document is ready for merge
- The dashboard shows "マージ待ちリスト" entries
- After ⑤ verification is approved and the phase is complete

## Prerequisites

Before merging, verify:
- [ ] The diff document has `status: approved`
- [ ] The diff document has `doc-kind: diff`
- [ ] The diff document's `base-version` matches the current master's `version`
- [ ] If `approval-required: true`, `approved-by` and `approved-at` are populated

## Procedure

### Step 1: Identify Source and Target

1. Read the diff document's frontmatter:
   - `phase` → determines target directory under `docs/`
   - `process` → determines target filename (e.g., process 2 → `02-breakdown.md`)
   - `iteration` → confirms the source iteration
   - `base-version` → the master version this diff was built against
2. Determine the target master file path: `docs/{phase}/{process-filename}.md`
3. For detailed-design component files, the path includes `components/{compId}/`

### Step 2: Version Conflict Check

1. Read the master document's current `version`
2. Compare with the diff's `base-version`
3. If they don't match:
   - **STOP** — there is a version conflict
   - Report: "Version conflict: diff base-version {X} ≠ master version {Y}"
   - The diff must be rebased on the current master before merging
   - Update the diff's `base-version` and reconcile content differences

### Step 3: Merge Content

1. Read both the diff and master documents fully
2. Apply the diff's changes to the master:
   - **New sections**: Add to the master at the appropriate location
   - **Modified sections**: Replace the corresponding section in master
   - **Deleted sections**: Remove from master (only if explicitly marked for deletion in diff)
   - **Tables**: Merge row-by-row; diff rows override master rows with matching IDs
3. Preserve any master content not addressed by the diff

### Step 4: Update Master Frontmatter

After content merge, update the master's frontmatter:

```yaml
version: "{incremented}"       # e.g., "1.0" → "1.1" (minor) or "2.0" (major)
status: draft                  # Reset to draft (unless this is the final merge of a gate doc)
updated-at: "YYYY-MM-DD"      # Current date
```

**Version increment rules:**
- Process ①②④: minor increment (1.0 → 1.1)
- Process ③⑤ (gate documents): minor increment, keep `status` as-is if `approved`
- Cross-iteration re-merge: major increment (1.x → 2.0)

### Step 5: Update Diff Document

Mark the diff as merged:

```yaml
status: merged                 # Custom status indicating merge complete
merged-at: "YYYY-MM-DD"       # Record merge timestamp
```

### Step 6: Post-Merge Validation

1. Verify the master document's YAML frontmatter is valid
2. Check that `input-refs` in the master are still correct (paths and versions)
3. Verify downstream documents' `input-refs` version references:
   - If master version changed from "1.0" to "1.1", downstream docs referencing version "1.0" need awareness (not necessarily immediate update)
4. Run a content consistency check:
   - All IDs (REQ-F-xxx, API-xxx, etc.) referenced in the document exist
   - Tables have no orphaned rows
   - Mermaid diagrams are syntactically valid

### Step 7: Update Dashboard

1. Remove the merged document from "差分ドキュメント マージ待ちリスト"
2. Update the status matrix if the merge changes any process status
3. Invoke `dashboard-sync` skill for the affected phase

## Merge Order for Multi-Process Phases

When multiple diff documents exist for the same phase, merge in process order:

```
01-validation.md → 02-breakdown.md → 03-decisions.md → 04-artifact.md → 05-verification.md
```

For detailed-design, follow the layer hierarchy:
```
02-breakdown-overview.md
  → components/{compId}/02-breakdown-{compId}.md (for each component)
  → 02-breakdown-validation.md
03-decisions-overview.md
  → components/{compId}/03-decisions-{compId}.md
04-artifact-overview.md
  → components/{compId}/04-artifact-{compId}.md
    → components/{compId}/04-artifact-{compId}-api.md
    → components/{compId}/04-artifact-{compId}-schema.md
    → components/{compId}/04-artifact-{compId}-domain.md
    → components/{compId}/04-artifact-{compId}-testcase.md
05-verification-overview.md
  → components/{compId}/05-verification-{compId}.md
```

## Conflict Resolution

If the same section is modified in both master (by another iteration's merge) and the current diff:

1. Present both versions to the user
2. Ask which version to keep, or request a manual reconciliation
3. Never silently overwrite — always flag conflicts

## Constraints

- Never merge a diff with `status` other than `approved`
- Never skip the version conflict check
- Always update the dashboard after merge
- If a merge fails mid-way, revert the master to its pre-merge state
