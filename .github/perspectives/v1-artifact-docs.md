# V1 Artifact Docs Static Checks

## Scope

- Target: docs/**/*.md
- Modes: artifact docs only
- Purpose: deterministic static checks before V2 perspective analysis

## Required Output Fields

- file_path
- check_id
- detection_method
- evidence_excerpt
- reason
- provisional_level

## Checkpoints

### V1-DOC-01: Heading hierarchy validity

Check:

- heading levels do not skip unexpectedly
- top-level heading exists

Detection method:

- parse markdown headings by level

Level rule:

- structural breakage -> Lv1

### V1-DOC-02: Unresolved placeholders

Check:

- TODO/TBD/XXX/[placeholder] remains in final artifact sections

Detection method:

- search placeholder token list

Level rule:

- unresolved placeholder in normative section -> Lv1

### V1-DOC-03: Reference consistency

Check:

- internal references point to existing headings or files

Detection method:

- search markdown links and verify target existence by path or anchor pattern

Level rule:

- definitely broken link/reference -> Lv1
- uncertain cross-doc reference -> Lv2

### V1-DOC-04: Requirement contradiction hints

Check:

- same requirement id or term has opposing directives in same document

Detection method:

- search paired antonym directives (must/must not) near same subject

Level rule:

- explicit contradiction -> Lv2
