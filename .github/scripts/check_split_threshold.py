#!/usr/bin/env python3
"""I-1: check-split-threshold — Check if iteration splitting is required.

Usage:
  python check_split_threshold.py [--breakdown docs/requirements/02-breakdown.md]

Thresholds:
  REQ-F count       > 15
  Subsystem count   > 2
  COMP-ID count     > 5
  High-priority NFR > 3

Output: JSON  { success, split_required, counts, thresholds, triggers }
"""
import sys, os, re, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _lib

_S = "I-1:check-split-threshold"

_THRESHOLDS = {
    "req_f": 15,
    "subsystems": 2,
    "comp_ids": 5,
    "nfr_high": 3,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--breakdown", default="docs/requirements/02-breakdown.md",
                    help="Breakdown document to analyse")
    args = ap.parse_args()

    _lib.debug_log(_S, "start", file=args.breakdown)

    text = _lib.read_text(args.breakdown)
    if text is None:
        _lib.out_err(f"Cannot read {args.breakdown}")

    req_f = set(re.findall(r"REQ-F-\d+", text))
    comp_ids = set(re.findall(r"COMP-\d+", text))
    subsystems = set(re.findall(r"(?:SUB|サブシステム)[- ]?\d+", text, re.IGNORECASE))

    nfr_high = set()
    for line in text.split("\n"):
        if re.search(r"REQ-NF", line) and re.search(r"High|Must|高", line, re.IGNORECASE):
            m = re.search(r"REQ-NF-\d+", line)
            if m:
                nfr_high.add(m.group(0))

    counts = {
        "req_f": len(req_f),
        "subsystems": max(len(subsystems), 1),
        "comp_ids": len(comp_ids),
        "nfr_high": len(nfr_high),
    }

    triggers = []
    for key, thresh in _THRESHOLDS.items():
        if counts[key] > thresh:
            triggers.append({"metric": key, "count": counts[key], "threshold": thresh})

    split_required = len(triggers) > 0
    _lib.debug_log(_S, "done", counts=counts, split=split_required)
    _lib.out_json({
        "success": True,
        "split_required": split_required,
        "counts": counts,
        "thresholds": _THRESHOLDS,
        "triggers": triggers,
    })


if __name__ == "__main__":
    main()
