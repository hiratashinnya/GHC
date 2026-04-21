"""Phase and process path helpers."""

import os
from pathlib import Path

from ._config import DD_OVERVIEW, PROC_FILE
from ._io import norm


def phase_path(phase, docs="docs"):
    """Return normalised path to a phase directory."""
    return norm(os.path.join(docs, phase))


def proc_filepath(phase, proc_num, docs="docs"):
    """Return docs-relative path for a process document."""
    fmap = DD_OVERVIEW if phase == "detailed-design" else PROC_FILE
    return norm(os.path.join(docs, phase, fmap.get(proc_num, "")))


def list_dd_components(docs="docs"):
    """List component .md files under detailed-design/components/."""
    cdir = Path(docs) / "detailed-design" / "components"
    if not cdir.exists():
        return []
    return sorted(norm(p) for p in cdir.rglob("*.md"))


def list_dd_comp_ids(docs="docs"):
    """List component directory names under detailed-design/components/."""
    cdir = Path(docs) / "detailed-design" / "components"
    if not cdir.is_dir():
        return []
    return sorted(d.name for d in cdir.iterdir() if d.is_dir())
