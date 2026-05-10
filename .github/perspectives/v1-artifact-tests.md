# V1 Artifact Tests Static Checks

## Scope

- Target: TestHooks/**/test_*.py, testcase.md, testresult.md
- Modes: artifact tests only
- Purpose: deterministic consistency checks for test triad

## Required Output Fields

- file_path
- check_id
- detection_method
- evidence_excerpt
- reason
- provisional_level

## Checkpoints

### V1-TST-01: Triad completeness

Check:

- each test module has test_*.py, testcase.md, testresult.md

Detection method:

- verify sibling file set in each test folder

Level rule:

- missing file in triad -> Lv1

### V1-TST-02: Testcase to test code traceability

Check:

- testcase ids appear in test code names or comments

Detection method:

- extract ids from testcase and search in test_*.py

Level rule:

- missing trace for defined case -> Lv1

### V1-TST-03: Result freshness markers

Check:

- testresult has execution date and commit id fields

Detection method:

- search lines containing 実行日: and コミットID:

Level rule:

- missing mandatory field -> Lv1

### V1-TST-04: Expected and actual pairing

Check:

- testresult entries include expected and outcome or pass/fail marker

Detection method:

- scan per-case result blocks for paired fields

Level rule:

- incomplete result record -> Lv1
