# V1 Customization Static Checks

## Scope

- Target: .github customization files only
- Modes: customization only
- Purpose: deterministic static checks for Lv1 pre-filter

## Required Output Fields

- file_path
- check_id
- detection_method
- evidence_excerpt
- reason
- provisional_level

## Checkpoints

### V1-CUS-01: Frontmatter integrity

Check:

- starts with --- and closes with ---
- name and description fields exist
- description is quoted when colon is included

Detection method:

- read first 40 lines and parse key fields

Level rule:

- missing required field or malformed delimiters -> Lv1

### V1-CUS-02: Name-path consistency

Check:

- name matches file base name or skill directory name

Detection method:

- compare file path and frontmatter name

Level rule:

- mismatch -> Lv1

### V1-CUS-03: Ambiguous constraint language

Check:

- detect vague terms in mandatory constraints (examples: 適切に, 必要に応じて)

Detection method:

- search for banned vague term list

Level rule:

- found in normative sentence -> Lv1

### V1-CUS-04: Duplicate or conflicting constraints

Check:

- duplicate rules with same semantics
- direct contradiction between MUST/DO NOT rules

Detection method:

- search repeated phrases and compare opposite directives

Level rule:

- exact duplicate -> Lv1
- possible contradiction requiring interpretation -> Lv2

### V1-CUS-05: Stage sequence consistency

Check:

- stage order text does not conflict with required workflow order

Detection method:

- read sequence section and compare with declared mandatory order

Level rule:

- explicit order violation -> Lv1
- unclear but plausible mismatch -> Lv2
