#!/usr/bin/env python3
"""H-1: check-phase-gate - block writes when required gate docs are not approved.

Usage:
  python .github/hooks/scripts/check_phase_gate.py [--target-path <path>] [--docs-dir docs] [--iter-dir iter]

Output:
  JSON { success, blocked, target, violations, missing_requirements }
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from debug_logging import HookDebugLogger


PHASES = [
    "requirements",
    "basic-design",
    "detailed-design",
    "implementation",
    "testing",
    "release",
]
PHASE_TO_INDEX = {name: i + 1 for i, name in enumerate(PHASES)}

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "check_phase_gate")


def out_json(data: Dict) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _scalar(raw: str):
    s = raw.strip()
    if not s:
        return None
    if len(s) >= 2 and ((s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'")):
        return s[1:-1]
    if s in ("true", "True", "yes"):
        return True
    if s in ("false", "False", "no"):
        return False
    if s in ("null", "~"):
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def parse_frontmatter(path: Path) -> Optional[Dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return None

    data: Dict = {}
    lines = m.group(1).split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s or s.startswith("#"):
            i += 1
            continue
        if line[:1].isspace() or ":" not in s:
            i += 1
            continue

        key, rest = s.split(":", 1)
        key = key.strip()
        rest = rest.strip()

        if rest == "":
            items = []
            i += 1
            while i < len(lines) and lines[i][:1] in (" ", "\t"):
                sl = lines[i].strip()
                if sl.startswith("- "):
                    items.append(_scalar(sl[2:].strip()))
                i += 1
            data[key] = items
            continue

        data[key] = _scalar(rest)
        i += 1

    data["_path"] = str(path).replace("\\", "/")
    return data


def infer_process(filename: str) -> Optional[int]:
    # Handles: 01-validation.md, 03-decisions-overview.md,
    # 04-artifact-<comp>.md, 05-verification-<comp>.md, etc.
    m = re.match(r"^(0[1-5])-", filename)
    if not m:
        return None
    return int(m.group(1))


def parse_target(target_path: str) -> Optional[Dict]:
    p = target_path.replace("\\", "/").strip("/")
    parts = p.split("/")

    if len(parts) >= 3 and parts[0] == "docs":
        phase = parts[1]
        proc = infer_process(parts[-1])
        if phase in PHASE_TO_INDEX and proc is not None:
            return {
                "scope": "docs",
                "phase": phase,
                "phase_index": PHASE_TO_INDEX[phase],
                "process": proc,
                "iteration": 0,
                "target_path": p,
            }

    if len(parts) >= 4 and parts[0] == "iter" and parts[1].startswith("iter") and parts[2].startswith("phase"):
        iter_raw = parts[1].replace("iter", "")
        phase_raw = parts[2].replace("phase", "")
        proc = infer_process(parts[-1])
        if iter_raw.isdigit() and phase_raw.isdigit() and proc is not None:
            phase_index = int(phase_raw)
            if 1 <= phase_index <= len(PHASES):
                phase = PHASES[phase_index - 1]
                return {
                    "scope": "iter",
                    "phase": phase,
                    "phase_index": phase_index,
                    "process": proc,
                    "iteration": int(iter_raw),
                    "target_path": p,
                }

    return None


def collect_gate_docs(docs_dir: Path, iter_dir: Path) -> List[Dict]:
    items: List[Dict] = []

    for root in (docs_dir, iter_dir):
        if not root.exists():
            continue
        for md in sorted(root.rglob("*.md")):
            if md.name == "dashboard.md":
                continue
            fm = parse_frontmatter(md)
            if not fm:
                continue
            if fm.get("approval-required") is not True:
                continue

            phase = fm.get("phase")
            process = fm.get("process")
            iteration = fm.get("iteration")

            try:
                process = int(process) if process is not None else None
            except ValueError:
                process = None
            try:
                iteration = int(iteration) if iteration is not None else 0
            except ValueError:
                iteration = 0

            items.append(
                {
                    "path": str(md).replace("\\", "/"),
                    "phase": phase,
                    "process": process,
                    "iteration": iteration,
                    "status": fm.get("status"),
                }
            )

    return items


def required_gate_specs(target: Dict) -> List[Tuple[str, int, Optional[int]]]:
    specs: List[Tuple[str, int, Optional[int]]] = []
    phase = target["phase"]
    phase_index = target["phase_index"]
    process = target["process"]
    iteration = target["iteration"]

    # Moving into a new phase's process 1 requires previous phase process 5 approval.
    if process == 1 and phase_index > 1:
        prev_phase = PHASES[phase_index - 2]
        prev_iter = iteration if target["scope"] == "iter" else 0
        specs.append((prev_phase, 5, prev_iter))

    # Process 4 and 5 require process 3 approval in the same phase.
    if process >= 4:
        req_iter = iteration if target["scope"] == "iter" else 0
        specs.append((phase, 3, req_iter))

    return specs


def evaluate(target: Dict, gate_docs: List[Dict]) -> Dict:
    specs = required_gate_specs(target)
    violations = []
    missing = []

    for phase, process, iteration in specs:
        matches = [
            g
            for g in gate_docs
            if g.get("phase") == phase
            and g.get("process") == process
            and (iteration is None or g.get("iteration") == iteration)
        ]

        if not matches:
            missing.append({"phase": phase, "process": process, "iteration": iteration})
            continue

        for g in matches:
            if g.get("status") != "approved":
                violations.append(g)

    blocked = bool(violations or missing)
    return {
        "blocked": blocked,
        "violations": violations,
        "missing_requirements": missing,
        "requirements": [
            {"phase": p, "process": pr, "iteration": it} for p, pr, it in specs
        ],
    }


def resolve_target_path(cli_target: Optional[str]) -> Optional[str]:
    if cli_target:
        return cli_target

    # Optional environment fallback for hook runners.
    env_keys = [
        "TARGET_PATH",
        "FILE_PATH",
        "TOOL_TARGET_PATH",
        "COPILOT_TARGET_PATH",
    ]
    for key in env_keys:
        val = os.getenv(key)
        if val:
            return val
    return None


def _read_hook_input() -> Optional[Dict]:
    """Read hook payload from stdin when available."""
    if sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read().strip()
    except OSError:
        return None
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _collect_paths(obj, out: List[str]) -> None:
    """Collect likely file paths from nested tool_input data."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if isinstance(v, str) and lk in {
                "filepath",
                "file_path",
                "path",
                "targetpath",
                "target_path",
            }:
                out.append(v)
            else:
                _collect_paths(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _collect_paths(item, out)


def _paths_from_hook_input(payload: Optional[Dict]) -> List[str]:
    if not payload:
        return []
    out: List[str] = []
    _collect_paths(payload.get("tool_input", {}), out)
    dedup = []
    seen = set()
    for p in out:
        n = p.replace("\\", "/")
        if n not in seen:
            seen.add(n)
            dedup.append(p)
    return dedup


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-path", default=None)
    ap.add_argument("--docs-dir", default="docs")
    ap.add_argument("--iter-dir", default="iter")
    args = ap.parse_args()

    hook_payload = _read_hook_input()
    targets = _paths_from_hook_input(hook_payload)

    # CLI and env fallbacks for manual testing.
    fallback = resolve_target_path(args.target_path)
    if fallback:
        targets.append(fallback)

    dedup_targets = []
    seen_targets = set()
    for t in targets:
        n = t.replace("\\", "/")
        if n not in seen_targets:
            seen_targets.add(n)
            dedup_targets.append(t)

    DEBUG.log(
        "start",
        target_count=len(dedup_targets),
        docs_dir=args.docs_dir,
        iter_dir=args.iter_dir,
    )

    if not dedup_targets:
        out_json({"success": True, "blocked": False, "message": "No target path provided"})
        return

    gate_docs = collect_gate_docs(Path(args.docs_dir), Path(args.iter_dir))

    evaluations = []
    blocked = False
    for path in dedup_targets:
        target = parse_target(path)
        if not target:
            continue
        result = evaluate(target, gate_docs)
        evaluations.append(
            {
                "target": target,
                "requirements": result["requirements"],
                "violations": result["violations"],
                "missing_requirements": result["missing_requirements"],
                "blocked": result["blocked"],
            }
        )
        blocked = blocked or result["blocked"]

    if not evaluations:
        out_json(
            {
                "success": True,
                "blocked": False,
                "message": "No docs/iter targets detected",
                "targets": dedup_targets,
            }
        )
        return

    payload = {
        "success": not blocked,
        "blocked": blocked,
        "evaluations": evaluations,
    }

    DEBUG.log(
        "done",
        blocked=blocked,
        checked=len(evaluations),
    )
    out_json(payload)

    if blocked:
        sys.exit(2)


if __name__ == "__main__":
    main()
