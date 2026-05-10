# V1 Artifact Code Static Checks

## Scope

- Target: src/**/*.py
- Modes: artifact code only
- Purpose: deterministic static sanity checks before semantic review

## Required Output Fields

- file_path
- check_id
- detection_method
- evidence_excerpt
- reason
- provisional_level

## Checkpoints

### V1-CODE-01: Syntax and import sanity

Check:

- obvious syntax issues and unresolved local imports patterns

Detection method:

- read file and inspect malformed blocks/import statements

Level rule:

- clear syntax/import error pattern -> Lv1

### V1-CODE-02: Unsafe broad exception use

Check:

- bare except or blanket exception swallowing without reason

Detection method:

- search for except: and except Exception with pass-only handling

Level rule:

- unsafe swallow pattern -> Lv1

### V1-CODE-03: Dead code markers

Check:

- commented-out code blocks or placeholder return/pass in production path

Detection method:

- search common dead-code markers

Level rule:

- placeholder logic in active path -> Lv1

### V1-CODE-04: Public API naming mismatch hints

Check:

- function/class names inconsistent with referenced spec terms in same file

Detection method:

- compare declared symbols and nearby spec keywords/comments

Level rule:

- clear mismatch with declared intent -> Lv2

### V1-CODE-05: Indentation and block consistency

Check:

- mixed indentation style causing logical ambiguity

Detection method:

- inspect indentation transitions and malformed block alignment

Level rule:

- structural indentation issue -> Lv1
