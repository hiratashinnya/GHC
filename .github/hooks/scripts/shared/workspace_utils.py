#!/usr/bin/env python3
"""workspace_utils.py — Workspace-aware path utilities for hook scripts.

Centralizes path normalization logic that is needed across multiple hook
scripts.  All functions are pure (no I/O, no side effects) so they can be
used freely in Skip-checks and other hot paths.

Typical usage::

    from workspace_utils import to_workspace_relative, is_under_dir, dedup_paths

    rel = to_workspace_relative(raw_path, workspace_path)
    if rel and is_under_dir(raw_path, "docs", workspace_path):
        ...
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

_LIB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "scripts"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

from _lib._io import norm  # noqa: E402


def to_workspace_relative(path: str, workspace_path: Path) -> Optional[str]:
    """Convert a path to a workspace-relative POSIX string.

    Accepts both absolute paths and paths relative to workspace_path.
    Returns None if the resolved path falls outside workspace_path.
    The returned string always uses forward slashes and has no leading slash.
    """
    p = Path(path) if Path(path).is_absolute() else workspace_path / path
    try:
        return p.resolve().relative_to(workspace_path.resolve()).as_posix()
    except ValueError:
        return None


def is_under_dir(path: str, subdir: str, workspace_path: Path) -> bool:
    """Return True if path is under workspace_path / subdir.

    subdir is a workspace-relative directory name (e.g. "docs", "iter").
    Both exact match (path == subdir) and descendant paths are accepted.
    """
    rel = to_workspace_relative(path, workspace_path)
    if rel is None:
        return False
    prefix = norm(subdir).rstrip("/")
    return rel == prefix or rel.startswith(prefix + "/")


def dedup_paths(paths: List[str]) -> List[str]:
    """Deduplicate paths preserving insertion order.

    Comparison is performed on POSIX-normalized strings (backslashes
    converted to forward slashes).  The returned list always contains
    POSIX-normalized strings.
    """
    seen: set[str] = set()
    result: List[str] = []
    for p in paths:
        key = norm(p)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result
