#!/usr/bin/env python3
"""hook_input.py — Input helpers for VS Code Copilot hook scripts."""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, Optional
from debug_logging import HookDebugLogger

_DECODE_CHAIN = ("utf-8", "cp932")


def read_payload(debug: Optional[HookDebugLogger] = None) -> Dict[str, Any]:
    """Read the hook payload from stdin and return it as a plain dict."""
    if sys.stdin.isatty():
        return {}
    try:
        raw_bytes = sys.stdin.buffer.read()
    except OSError as exc:
        print(f"[hook_payload] stdin read error: {exc}", file=sys.stderr)
        return {}
    if not raw_bytes:
        return {}

    raw = ""
    for encoding in _DECODE_CHAIN:
        try:
            raw = raw_bytes.decode(encoding).strip()
            break
        except UnicodeDecodeError:
            continue
    else:
        raw = raw_bytes.decode("utf-8", errors="replace").strip()
        print(
            f"[hook_payload] payload decoding failed for all encodings "
            f"{_DECODE_CHAIN}; decoded with replacement characters",
            file=sys.stderr,
        )

    if debug:
        debug.log("input_raw", raw=raw)
        
    if not raw:
        return {}
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[hook_payload] JSON parse error: {exc}", file=sys.stderr)
        return {}



