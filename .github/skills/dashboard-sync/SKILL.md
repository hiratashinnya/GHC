---
name: dashboard-sync
description: "Use when updating or verifying docs/dashboard.md after document status changes. Synchronizes the dashboard status matrix and component progress with actual document frontmatter. Trigger phrases: dashboard sync, dashboard update, dashboard check, sync dashboard, verify dashboard, refresh dashboard, dashboard consistency"
argument-hint: "Specify phase: requirements | basic-design | detailed-design | implementation | testing | release"
---

# Dashboard Sync

Synchronize `docs/dashboard.md` with actual document frontmatter status across all phases. The orchestrator invokes this skill at phase transitions and after document status changes.

## When to Use

- Before starting any new work (verify dashboard reflects reality)
- After a document's `status` field changes
- At phase/process transitions
- When the orchestrator detects dashboard inconsistency
- After session resumption to restore state

## Common Procedure (All Phases)

### Step 1: Scan Documents

1. Read `docs/dashboard.md` current state
2. Scan all `.md` files under `docs/{phase}/` and read their YAML frontmatter
3. For each file, extract: `doc-type`, `process`, `status`, `approval-required`, `approved-at`

### Step 2: Map Status to Emoji

| `status` value | Dashboard symbol |
|---------------|-----------------|
| `approved` | ✅ |
| `awaiting-approval` | ⏳ |
| `draft` | 📝 |
| `rejected` | ❌ |
| `under-revision` | 🔙 |
| (file not yet created) | ─ |

### Step 3: Update Status Matrix

1. Locate the phase's row in the "フェーズ × プロセス ステータスマトリクス" table
2. Update columns ① through ⑤ based on scanned status
3. The ②v column is ─ for all phases except detailed-design

### Step 4: Update Bottlenecks

1. Collect all documents where `approval-required: true` AND `status` is NOT `approved`
2. Collect all documents where `status: rejected`
3. Collect all documents where `status: under-revision` (rollback impact)
4. List these in the ボトルネック section with file path and status

### Step 5: Update Next Actions

Based on the current state, determine and write the next recommended action.

### Step 6: Update Metadata

1. Set `last-updated` to current datetime (`YYYY-MM-DD HH:MM`)
2. Update "現在のフェーズ" and "現在のプロセス" in プロジェクト基本情報

---

## Phase-Specific Procedures

### requirements (Phase 1)

**Documents to scan:**
- `docs/requirements/01-validation.md` → column ①
- `docs/requirements/02-breakdown.md` → column ②
- `docs/requirements/03-decisions.md` → column ③
- `docs/requirements/04-artifact.md` → column ④
- `docs/requirements/05-verification.md` → column ⑤

**Additional checks:**
- Verify iteration scope files exist under `docs/requirements/iterations/`
- For each `04-artifact-iterN.md`, confirm it is referenced in `04-artifact.md`'s イテレーション別ファイルリンク table
- ②v column → always ─

---

### basic-design (Phase 2)

**Documents to scan:**
- `docs/basic-design/01-validation.md` → column ①
- `docs/basic-design/02-breakdown.md` → column ②
- `docs/basic-design/03-decisions.md` → column ③
- `docs/basic-design/04-artifact.md` → column ④
- `docs/basic-design/05-verification.md` → column ⑤

**Additional checks:**
- Verify component specifications (COMP-ID) in `04-artifact.md` are complete
- Check that コンポーネント仕様 table has all fields populated
- ②v column → always ─

---

### detailed-design (Phase 3)

**Documents to scan:**
- `docs/detailed-design/01-validation.md` → column ①
- `docs/detailed-design/02-breakdown-overview.md` → column ②
- `docs/detailed-design/02-breakdown-validation.md` → column ②v
- `docs/detailed-design/03-decisions-overview.md` → column ③
- `docs/detailed-design/04-artifact-overview.md` → column ④
- `docs/detailed-design/05-verification-overview.md` → column ⑤

**Component-level progress table update:**

For each `{compId}` directory under `docs/detailed-design/components/`:

1. Read `components/{compId}/02-breakdown-{compId}.md` → ②分解 column
2. Read `components/{compId}/03-decisions-{compId}.md` → ③決定 column
3. Read `components/{compId}/04-artifact-{compId}.md` → ④サマリ column
4. Read `components/{compId}/04-artifact-{compId}-api.md` → ④API column
5. Read `components/{compId}/04-artifact-{compId}-schema.md` → ④Schema column
6. Read `components/{compId}/04-artifact-{compId}-domain.md` → ④Domain column
7. Read `components/{compId}/04-artifact-{compId}-testcase.md` → ④TestCase column
8. Read `components/{compId}/05-verification-{compId}.md` → ⑤検証 column

Update the "詳細設計 コンポーネント別進捗" table accordingly.

**If a new component is found** (directory exists but no row in table): add a new row.

---

### implementation (Phase 4)

**Documents to scan:**
- `docs/implementation/01-validation.md` → column ①
- `docs/implementation/02-breakdown.md` → column ②
- `docs/implementation/03-decisions.md` → column ③
- `docs/implementation/04-artifact.md` → column ④
- `docs/implementation/05-verification.md` → column ⑤

**Additional checks:**
- Read `docs/implementation/02-breakdown.md` for task completion stats
- Count tasks by status (Done / In Progress / Not Started)
- If `04-artifact.md` exists, check テストパス率 section
- ②v column → always ─

---

### testing (Phase 5)

**Documents to scan:**
- `docs/testing/01-validation.md` → column ①
- `docs/testing/02-breakdown.md` → column ②
- `docs/testing/03-decisions.md` → column ③
- `docs/testing/04-artifact.md` → column ④
- `docs/testing/05-verification.md` → column ⑤

**Additional checks:**
- If `04-artifact.md` exists, check quality gate metrics (coverage, pass rate)
- Verify all test types defined in `03-decisions.md` have corresponding results in `04-artifact.md`
- ②v column → always ─

---

### release (Phase 6)

**Documents to scan:**
- `docs/release/01-validation.md` → column ①
- `docs/release/02-breakdown.md` → column ②
- `docs/release/03-decisions.md` → column ③
- `docs/release/04-artifact.md` → column ④
- `docs/release/05-verification.md` → column ⑤

**Additional checks:**
- If `04-artifact.md` exists, check deploy result and smoke test status
- Verify rollback plan is documented
- ②v column → always ─

---

## Iteration Handling

When the project has multiple iterations:
1. Check `docs/dashboard.md` イテレーション履歴 table
2. Update the current iteration's row with the latest status
3. The status matrix header shows the current iteration: "ステータスマトリクス（iterN）"
4. Component progress table header also shows: "コンポーネント別進捗（iterN）"

## Error Handling

- If a document file does not exist, set its column to ─ (not-started)
- If YAML frontmatter is malformed, report the file path as an error and skip it
- If dashboard itself is malformed, recreate from the template at `.github/templates/dashboard.md`
