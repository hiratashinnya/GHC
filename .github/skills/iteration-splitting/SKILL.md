---
name: iteration-splitting
description: "Use when determining how to split a large-scope project into multiple iterations. Provides criteria for iteration boundary decisions, scope allocation, and PRD file splitting. Trigger phrases: iteration split, scope split, iteration plan, divide iterations, MVP scope, iteration boundary, large project splitting"
argument-hint: "Describe the project scope or provide the requirements list to split"
---

# Iteration Splitting

Determine how to divide a large-scope project into multiple development iterations (iter1, iter2, ...). Each iteration covers Phases 2–6 (basic-design through release). Phase 1 (requirements) is executed once for all iterations.

## When to Use

- Project scope is too large for a single pass through Phases 2–6
- Multiple subsystems or feature groups exist
- The user or orchestrator needs to decide iteration boundaries
- During `requirements/03-decisions.md` authoring (scope splitting decisions)

## Splitting Criteria

### Mandatory Split Triggers

Split into multiple iterations when ANY of the following is true:

| Trigger | Threshold | Rationale |
| --------- | ----------- | ----------- |
| Functional requirements count | > 15 REQ-F items | Cognitive load per iteration |
| Independent subsystem count | > 2 subsystems | Parallel workstream isolation |
| Estimated component count | > 5 COMP-IDs | Design complexity management |
| Cross-cutting concerns | > 3 non-functional categories with HIGH priority | Risk isolation |

### Split Strategy

Use this priority order to assign features to iterations:

1. **iter1 (MVP)**: Core value proposition + minimum viable feature set
   - Must-have functional requirements (Priority: Must)
   - The smallest set that delivers user-facing value end-to-end
   - Critical non-functional requirements (security, basic performance)

2. **iter2+**: Incremental feature groups
   - Should-have requirements (Priority: Should)
   - Features with external dependencies that may delay
   - Performance optimization, advanced UX

3. **Final iteration**: Polish and edge cases
   - Could-have requirements (Priority: Could)
   - Monitoring, observability, admin tooling
   - Documentation refinement

### Dependency-Aware Ordering

```
For each candidate iteration:
  1. List all REQ-F items assigned to this iteration
  2. Check if any REQ-F depends on a REQ-F in a later iteration
     → If yes, move the dependency to an earlier iteration
  3. Check if any COMP-ID is shared across iterations
     → If yes, assign the component's core functionality to the earliest iteration
  4. Verify the iteration is self-contained (can be deployed independently)
```

## Procedure

### Step 1: Inventory Requirements

1. Read `docs/requirements/02-breakdown.md` for the full decomposition
2. List all REQ-F (functional) and REQ-NF (non-functional) items
3. Note dependencies from the dependency graph

### Step 2: Apply Splitting Criteria

1. Count requirements, subsystems, and components
2. If mandatory split triggers are met → proceed with splitting
3. If not → recommend single iteration (skip remaining steps)

### Step 3: Group Into Iterations

1. Assign Priority: Must items to iter1
2. Group remaining items by feature affinity (related requirements together)
3. Apply dependency ordering constraints
4. Target 5–10 REQ-F items per iteration (guideline, not hard limit)
5. Ensure each iteration has a coherent deployment unit

### Step 4: Document in 03-decisions.md

Record the iteration split in `docs/requirements/03-decisions.md`:

```markdown
## Iteration Scope Split

| Iteration | Theme | REQ-F IDs | REQ-NF IDs | Target COMP-IDs |
| ----------- | ------- | ----------- | ------------ | ---------------- |
| iter1 (MVP) | Core functionality | REQ-F-001, ... | REQ-NF-001, ... | COMP-001, ... |
| iter2 | Extended features | REQ-F-010, ... | | COMP-003, ... |
```

### Step 5: Create Iteration Artifact Files

For each iteration N:
1. Create `docs/requirements/iterations/04-artifact-iterN.md` from template
2. Populate with the assigned REQ-F items, user stories, and acceptance criteria
3. Update `docs/requirements/04-artifact.md` イテレーション別ファイルリンク table
4. Update `docs/dashboard.md` イテレーション履歴 table

### Step 6: Verify Completeness

- [ ] Every REQ-F is assigned to exactly one iteration
- [ ] Every REQ-NF is assigned or marked as cross-iteration
- [ ] No circular dependencies across iterations
- [ ] iter1 is independently deployable
- [ ] Each iteration file has correct `input-refs` to parent `04-artifact.md`

## Output

- Updated `docs/requirements/03-decisions.md` with scope split decision table
- Created `docs/requirements/iterations/04-artifact-iterN.md` for each iteration
- Updated `docs/requirements/04-artifact.md` links section
- Updated `docs/dashboard.md` iteration history

## Constraints

- Phase 1 (requirements) is always single-pass — never split requirements gathering itself
- Iteration boundaries must be decided and approved in `03-decisions.md` before proceeding
- Once approved, iteration scope is frozen for that iteration (changes require a new iteration or scope change request through ③)
