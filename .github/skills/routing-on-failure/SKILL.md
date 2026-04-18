---
name: routing-on-failure
description: "Use when ① input validation (01-validation.md) or ⑤ artifact verification (05-verification.md) results in NG (FAIL / CONDITIONAL PASS). Determines the correct rollback target process. Trigger phrases: NG routing, failure routing, rollback, reject, fail, remand, revert process, rework"
---

# NG Routing on Failure

Determine the rollback destination when a process outputs NG (FAIL or CONDITIONAL PASS). This skill is invoked by the orchestrator after ① or ⑤ produces a negative result.

## When to Use

- `01-validation.md` judge is FAIL or CONDITIONAL PASS
- `05-verification.md` judge is FAIL or CONDITIONAL PASS
- `02-breakdown-validation.md` (detailed-design ②v) judge is FAIL

## Procedure

### Step 1: Read the NG Document

1. Open the NG document (`01-validation.md`, `05-verification.md`, or `02-breakdown-validation.md`)
2. Read the 指摘事項 (findings) section
3. Classify each finding into one of the NG reason categories below

### Step 2: Determine Rollback Target

#### ① Input Validation NG (`01-validation.md`)

| NG Reason | Rollback Target | Action |
|-----------|----------------|--------|
| Previous phase artifact is incomplete or unapproved | Previous phase ④ or ⑤ | Complete/re-approve the previous phase artifact |
| Contradiction between previous phase artifacts | Previous phase ③ | Re-examine decisions |
| Requirements themselves are deficient (out of scope of previous phase) | `requirements/②` | Re-decompose/redefine requirements |

#### ⑤ Artifact Verification NG (`05-verification.md`)

| NG Reason | Rollback Target | Action |
|-----------|----------------|--------|
| Minor quality shortfall in artifact | Same phase ④ | Fix/supplement the artifact |
| Mismatch between decisions (③) and artifact | Same phase ③ | Re-examine decisions |
| Decomposition granularity/scope is inappropriate | Same phase ② | Redo decomposition |
| Upstream assumption is wrong | Previous phase's relevant process | Escalate upstream |

#### ②v Breakdown Validation NG (detailed-design only)

| NG Reason | Rollback Target | Action |
|-----------|----------------|--------|
| Component allocation missing (COMP-ID not mapped in ②-a) | `02-breakdown-overview.md` | Update component allocation matrix |
| Component breakdown not MECE (②-b has gaps/overlaps) | `components/{compId}/02-breakdown-{compId}.md` | Re-decompose the specific component |
| Requirements traceability broken | `02-breakdown-overview.md` | Fix traceability matrix |

### Step 3: Identify Impacted Downstream Documents

Determine all documents whose validity depends on the rollback target.

#### Cascade Scope Rules

**Same-phase rollback** (rollback target is in the same phase as the NG document):
- All documents with process number **greater than** the rollback target's process, within the same phase and iteration
- Example: rollback to ② → downstream = ③, ④, ⑤

**Cross-phase rollback** (rollback target is in a previous phase):
- Remaining processes after the rollback target in the target phase
- **All** processes (① through ⑤) in the current phase (same iteration)
- Example: rollback to previous phase ③ → downstream = previous phase ④, ⑤ + current phase ①–⑤

**Detailed-design sub-process rollback**:
- Rollback to `02-breakdown-overview.md` → all component `02-breakdown-{compId}.md` + `02-breakdown-validation.md` + ③, ④, ⑤
- Rollback to specific `02-breakdown-{compId}.md` → that component's `03-decisions-{compId}.md`, `04-artifact-{compId}.md` + `02-breakdown-validation.md`

#### Filter Criteria

Only mark documents that:
1. Already exist (have been created in a prior process run)
2. Have `status` of `draft`, `awaiting-approval`, or `approved`

Skip documents with `status: rejected` or `status: under-revision` (already invalidated).

### Step 4: Execute Rollback and Propagate Impact

#### 4a. Mark the NG Document

1. Set `status: rejected` on the NG document
2. Record the rollback reason in the 指摘事項 section with:
   - Finding ID
   - Severity (High / Mid / Low)
   - Target section
   - Description
   - Recommended action
   - Rollback destination path

#### 4b. Mark the Rollback Target

1. Set `status: under-revision` on the rollback target document
2. Add `"impacted-by-rollback"` to the `tags` array in its frontmatter (create `tags: []` if absent; append to existing tags)
3. Log the rollback in the rollback target document's 変更履歴

#### 4c. Propagate Impact to Downstream Documents

For each downstream document identified in Step 3:

1. Set `status: under-revision`
2. Add `"impacted-by-rollback"` to the `tags` array in frontmatter
3. Append an entry to the document's 変更履歴:
   - Date
   - Reason: `"Impacted by rollback of {rollback-target-path} triggered by {ng-document-path}"`

#### 4d. Update Dashboard

1. Run the `dashboard-sync` skill for each affected phase
2. Log the rollback event in the NG document's 変更履歴

### Step 5: Notify

Report to the orchestrator:
- Which document was NG
- The rollback destination (file path + process number)
- Summary of findings
- List of downstream documents marked as `under-revision` (file paths)
- Total count of impacted documents
- Whether human intervention is required (if rollback crosses a phase boundary)

## Decision Tree

```
NG Document received
│
├── Step 1-2: Determine rollback target
│   ├── 01-validation.md NG?
│   │   ├── Previous artifact incomplete? → Previous phase ④/⑤
│   │   ├── Previous artifacts contradict? → Previous phase ③
│   │   └── Requirements deficient? → requirements/②
│   ├── 05-verification.md NG?
│   │   ├── Minor quality issue? → Same phase ④
│   │   ├── Decision-artifact mismatch? → Same phase ③
│   │   ├── Decomposition issue? → Same phase ②
│   │   └── Upstream assumption wrong? → Previous phase (escalate)
│   └── 02-breakdown-validation.md NG?
│       ├── COMP-ID not mapped? → 02-breakdown-overview.md
│       ├── Component not MECE? → components/{compId}/02-breakdown-{compId}.md
│       └── Traceability broken? → 02-breakdown-overview.md
│
├── Step 3: Identify downstream cascade
│   ├── Same-phase? → Mark processes after target in same phase
│   ├── Cross-phase? → Mark target phase remainder + all current phase
│   └── Detailed-design sub-process? → Mark dependent components + ②v + ③④⑤
│
└── Step 4: Execute
    ├── NG document       → status: rejected
    ├── Rollback target   → status: under-revision + tags: ["impacted-by-rollback"]
    ├── Downstream docs   → status: under-revision + tags: ["impacted-by-rollback"]
    └── Dashboard         → sync all affected phases
```

## Constraints

- When rollback crosses a phase boundary, always notify the human operator
- Never skip intermediate processes when rolling back (e.g., don't go from ⑤ directly to ① of the same phase)
- If multiple NG reasons point to different rollback targets, choose the **furthest upstream** target
- After rollback completes and the target is re-approved, resume from that process forward (do not skip any subsequent processes)
- All downstream documents marked `under-revision` must be re-validated or re-approved before the workflow can proceed past them
- **Tag removal is staged** (two-phase):
  1. When the rollback target is re-approved → downstream documents' `status` changes from `under-revision` to `draft`; the `impacted-by-rollback` tag remains
  2. When each downstream document itself is re-validated/re-approved → remove the `impacted-by-rollback` tag from that document
- Cascade propagation is limited to documents within the **same iteration**; other iterations are not automatically impacted
- When removing the `impacted-by-rollback` tag, also verify that the document's `input-refs` versions still match the current upstream versions
