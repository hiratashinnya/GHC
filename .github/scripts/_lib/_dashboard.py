"""Dashboard status matrix and bottleneck builders."""

import os

from ._config import (
    PHASES, PHASE_LABEL, PROC_FILE, DD_OVERVIEW, DD_VALIDATION,
    STATUS_EMOJI, NOT_STARTED,
)
from ._frontmatter import parse_fm, scan_fm
from ._paths import list_dd_comp_ids


def _emoji_for(filepath):
    """Return status emoji for a document, or NOT_STARTED if missing."""
    if not os.path.exists(filepath):
        return NOT_STARTED
    fm = parse_fm(filepath)
    if not fm:
        return NOT_STARTED
    return STATUS_EMOJI.get(fm.get("status", ""), NOT_STARTED)


def build_matrix_md(docs="docs"):
    """Build the status-matrix Markdown table string."""
    hdr = "| フェーズ | ① 検証 | ② 分解 | ②v 分解検証 | ③ 意思決定 | ④ 成果物 | ⑤ 検証承認 |"
    sep = "|----------|---|---|-----|---|---|---|"
    rows = [hdr, sep]
    for idx, phase in enumerate(PHASES, start=1):
        pp = os.path.join(docs, phase)
        fmap = DD_OVERVIEW if phase == "detailed-design" else PROC_FILE
        cols = {p: _emoji_for(os.path.join(pp, fmap[p])) for p in range(1, 6)}
        cols["2v"] = (
            _emoji_for(os.path.join(pp, DD_VALIDATION))
            if phase == "detailed-design"
            else NOT_STARTED
        )
        label = f"フェーズ{idx}: {PHASE_LABEL.get(phase, phase)}"
        rows.append(
            f"| {label} | {cols[1]} | {cols[2]} | {cols['2v']}"
            f" | {cols[3]} | {cols[4]} | {cols[5]} |"
        )
    return "\n".join(rows)


def build_component_table_md(docs="docs"):
    """Build detailed-design component progress table or None."""
    comp_ids = list_dd_comp_ids(docs)
    if not comp_ids:
        return None
    dd = os.path.join(docs, "detailed-design", "components")
    hdr = "| コンポーネントID | ②分解 | ③決定 | ④サマリ | ④API | ④Schema | ④Domain | ④TestCase | ⑤検証 |"
    sep = "|-------------|------|------|---------|------|---------|---------|-----------|------|"
    rows = [hdr, sep]
    for cid in comp_ids:
        cd = os.path.join(dd, cid)
        e = lambda fn, _cd=cd: _emoji_for(os.path.join(_cd, fn))
        rows.append(
            f"| {cid}"
            f" | {e(f'02-breakdown-{cid}.md')}"
            f" | {e(f'03-decisions-{cid}.md')}"
            f" | {e(f'04-artifact-{cid}.md')}"
            f" | {e(f'04-artifact-{cid}-api.md')}"
            f" | {e(f'04-artifact-{cid}-schema.md')}"
            f" | {e(f'04-artifact-{cid}-domain.md')}"
            f" | {e(f'04-artifact-{cid}-testcase.md')}"
            f" | {e(f'05-verification-{cid}.md')}"
            f" |"
        )
    return "\n".join(rows)


def find_bottleneck_lines(docs="docs"):
    """Return list of bottleneck Markdown bullet lines."""
    items = []
    for fm in scan_fm(docs):
        st = fm.get("status", "")
        fp = fm.get("_path", "")
        ar = fm.get("approval-required", False)
        if st == "rejected":
            items.append(f"- `{fp}`: {st}（却下）")
        elif st == "under-revision":
            items.append(f"- `{fp}`: {st}（差し戻し影響）")
        elif ar and st != "approved":
            items.append(f"- `{fp}`: {st}（承認待ち）")
    return items
