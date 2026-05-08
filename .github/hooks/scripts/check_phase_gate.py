#!/usr/bin/env python3
"""H-1: check-phase-gate - block writes when required gate docs are not approved.

Usage:
  python .github/hooks/scripts/check_phase_gate.py [--target-path <path>]
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from debug_logging import HookDebugLogger
from hook_payload import read_payload, parse_payload, PreToolUsePayload
from tool_input import is_write_tool, get_written_paths
from workspace_utils import to_posix, dedup_paths


PHASES = [
    "requirements",
    "basic-design",
    "detailed-design",
    "implementation",
    "testing",
    "release",
]
PHASE_TO_INDEX = {name: i + 1 for i, name in enumerate(PHASES)}

PROCESS_NAMES = {
    1: "validation",
    2: "breakdown",
    3: "decisions",
    4: "artifact",
    5: "verification",
}
# process=4 専用サフィックス。variant 抽出時に compId と区別するために除去する。
ARTIFACT_SUBTYPES = {"api", "domain", "schema", "testcase"}

SCRIPT_DIR = Path(__file__).resolve().parent
DEBUG = HookDebugLogger(SCRIPT_DIR, "check_phase_gate")


@dataclass
class WorkflowIdentifier:
    """フェーズワークフロー内のドキュメント座標。"""
    phase: str
    process: int
    iteration: int
    variant: Optional[str]  # None | "overview" | "{compId}" | "iterN" など

    def preceding_gates(self) -> List[WorkflowIdentifier]:
        """このドキュメントを書き込む前に承認されていなければならないゲートの座標リストを返す。

        Rules:
        - process==1 かつ phase_index>1: 前フェーズの process 5 が必要。
        - process>=4 かつ variant が compId (None/"overview" 以外):
            同フェーズ process 3 の variant 版と overview 版の両方が必要。
        - process>=4 それ以外: 同フェーズ process 3 の同 variant が必要。
        """
        gates: List[WorkflowIdentifier] = []
        phase_index = PHASE_TO_INDEX.get(self.phase, 0)

        if self.process == 1 and phase_index > 1:
            prev_phase = PHASES[phase_index - 2]
            gates.append(WorkflowIdentifier(
                phase=prev_phase, process=5, iteration=self.iteration, variant=None
            ))

        if self.process >= 4:
            is_comp_id = self.variant is not None and self.variant != "overview"
            gates.append(WorkflowIdentifier(
                phase=self.phase, process=3, iteration=self.iteration, variant=self.variant
            ))
            if is_comp_id:
                gates.append(WorkflowIdentifier(
                    phase=self.phase, process=3, iteration=self.iteration, variant="overview"
                ))

        return gates


@dataclass
class WorkflowDocument:
    """フェーズワークフロー内の実ドキュメント。"""
    scope: str                # "docs" | "iter"
    idx: WorkflowIdentifier
    path: Optional[str]       # None = ファイルが存在しない

    def exists(self) -> bool:
        return self.path is not None

    def _expected_path(self) -> str:
        """命名規則に基づく期待パスを返す。"""
        name = PROCESS_NAMES[self.idx.process]
        suffix = f"-{self.idx.variant}" if self.idx.variant else ""
        phase_idx = PHASE_TO_INDEX.get(self.idx.phase, 0)

        if self.scope == "iter":
            return f"iter/iter{self.idx.iteration}/phase{phase_idx}/0{self.idx.process}-{name}{suffix}.md"

        # docs scope
        if (
            self.idx.phase == "detailed-design"
            and self.idx.variant is not None
            and self.idx.variant != "overview"
        ):
            # compId あり → components/{compId}/ サブディレクトリ
            return f"docs/detailed-design/components/{self.idx.variant}/0{self.idx.process}-{name}-{self.idx.variant}.md"

        return f"docs/{self.idx.phase}/0{self.idx.process}-{name}{suffix}.md"

    def approved(self) -> bool:
        """フロントマターの status が "approved" であるか確認する。"""
        if not self.path:
            return False
        fm = parse_frontmatter(Path(self.path))
        return bool(fm and fm.get("status") == "approved")


@dataclass
class GateCheckResult:
    """1件の WorkflowDocument に対するゲートチェック結果。"""
    target: WorkflowDocument
    blocked: bool
    violations: List[WorkflowDocument]         # 存在するが未承認
    missing: List[WorkflowDocument]            # ファイルが存在しない
    naming_violations: List[WorkflowDocument]  # glob で発見したが命名規則違反


def _scalar(raw: str):
    s = raw.strip()
    if not s:
        return None
    
    # "foo" -> foo, 'bar' -> bar, but "foo -> "foo and foo" -> foo"
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


def parse_frontmatter(path: Path) -> Optional[Dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return None

    data: Dict[str, Any] = {}
    lines = m.group(1).split("\n")
    i = 0
    
    # Simple YAML-like frontmatter parser supporting key: value pairs and lists (key: \n  - item1\n  - item2).
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        # Skip empty lines and comments
        if not s or s.startswith("#"):
            i += 1
            continue
        # Skip lines that don't contain a key (no colon) or are indented (list items or continuation lines)
        if line[:1].isspace() or ":" not in s:
            i += 1
            continue

        # Parse key and value
        key, rest = s.split(":", 1)
        key = key.strip()
        rest = rest.strip()

        # If rest is empty, check for list items in the following indented lines
        if rest == "":
            items = []
            i += 1
            # Collect indented list items (starting with "- ") until the next non-indented line
            while i < len(lines) and lines[i][:1] in (" ", "\t"):
                sl = lines[i].strip()
                if sl.startswith("- "):
                    items.append(_scalar(sl[2:].strip()))
                i += 1
            data[key] = items
            continue

        data[key] = _scalar(rest)
        i += 1

    data["_path"] = to_posix(str(path))
    return data


def infer_process(filename: str) -> Optional[int]:
    # Handles: 01-validation.md, 03-decisions-overview.md,
    # 04-artifact-<comp>.md, 05-verification-<comp>.md, etc.
    m = re.match(r"^(0[1-5])-", filename)
    if not m:
        return None
    return int(m.group(1))


def _extract_variant(filename: str, process: int) -> Optional[str]:
    """ファイル名からvariantを抽出する。

    e.g. "03-decisions-overview.md" -> "overview"
         "04-artifact-auth-api.md"  -> "auth"  (ARTIFACT_SUBTYPESを除去)
         "01-validation.md"         -> None
    """
    name = PROCESS_NAMES.get(process, "")
    # prefix: "0N-name-" を除いた残り
    prefix = f"0{process}-{name}-"
    if not filename.startswith(prefix) or not filename.endswith(".md"):
        return None
    rest = filename[len(prefix):-3]  # .md を除く
    if not rest:
        return None
    # process=4 のサブタイプ（api/domain/schema/testcase）を末尾から除去
    if process == 4:
        parts = rest.rsplit("-", 1)
        if len(parts) == 2 and parts[1] in ARTIFACT_SUBTYPES:
            rest = parts[0]
    return rest if rest else None


def _parse_docs_target(parts: list, p: str) -> Optional[WorkflowDocument]:
    """docs/ パスを解析して WorkflowDocument を返す。"""
    if len(parts) < 3:
        return None
    phase = parts[1]
    if phase not in PHASE_TO_INDEX:
        return None

    # docs/detailed-design/components/{compId}/0N-name-{compId}.md
    if phase == "detailed-design" and len(parts) >= 5 and parts[2] == "components":
        comp_id = parts[3]
        proc = infer_process(parts[-1])
        if proc is None:
            return None
        return WorkflowDocument(
            scope="docs",
            idx=WorkflowIdentifier(phase=phase, process=proc, iteration=0, variant=comp_id),
            path=p,
        )

    # docs/{phase}/0N-name{-variant}.md
    proc = infer_process(parts[-1])
    if proc is None:
        return None
    return WorkflowDocument(
        scope="docs",
        idx=WorkflowIdentifier(phase=phase, process=proc, iteration=0, variant=_extract_variant(parts[-1], proc)),
        path=p,
    )


def _parse_iter_target(parts: list, p: str) -> Optional[WorkflowDocument]:
    """iter/ パスを解析して WorkflowDocument を返す。"""
    if len(parts) < 4 or not parts[1].startswith("iter") or not parts[2].startswith("phase"):
        return None
    iter_raw = parts[1][4:]
    phase_raw = parts[2][5:]
    if not iter_raw.isdigit() or not phase_raw.isdigit():
        return None
    phase_index = int(phase_raw)
    if not (1 <= phase_index <= len(PHASES)):
        return None
    proc = infer_process(parts[-1])
    if proc is None:
        return None
    return WorkflowDocument(
        scope="iter",
        idx=WorkflowIdentifier(
            phase=PHASES[phase_index - 1],
            process=proc,
            iteration=int(iter_raw),
            variant=_extract_variant(parts[-1], proc),
        ),
        path=p,
    )


def parse_write_target(target_path: str) -> Optional[WorkflowDocument]:
    """書き込みパスを解析して WorkflowDocument を返す。

    対応パターン:
      docs/{phase}/0N-name{-variant}.md
      docs/detailed-design/components/{compId}/0N-name-{compId}.md
      iter/iter{N}/phase{M}/0N-name{-variant}.md
    """
    p = to_posix(target_path).strip("/")
    parts = p.split("/")
    if parts[0] == "docs":
        return _parse_docs_target(parts, p)
    if parts[0] == "iter":
        return _parse_iter_target(parts, p)
    return None


def _find_gate_file(scope: str, gate_id: WorkflowIdentifier) -> Optional[str]:
    """ゲート座標に対応するファイルを glob で検索する（命名規則違反検出用）。"""
    name = PROCESS_NAMES.get(gate_id.process, "")
    if scope == "iter":
        phase_idx = PHASE_TO_INDEX.get(gate_id.phase, 0)
        pattern = f"iter/iter{gate_id.iteration}/phase{phase_idx}/0{gate_id.process}-{name}-*.md"
        fallback = f"iter/iter{gate_id.iteration}/phase{phase_idx}/0{gate_id.process}-{name}.md"
    elif gate_id.phase == "detailed-design" and gate_id.variant not in (None, "overview"):
        pattern = f"docs/detailed-design/components/{gate_id.variant}/0{gate_id.process}-{name}-*.md"
        fallback = None
    else:
        pattern = f"docs/{gate_id.phase}/0{gate_id.process}-{name}-*.md"
        fallback = f"docs/{gate_id.phase}/0{gate_id.process}-{name}.md"

    # fallback (variant なしファイル) を先に確認
    if fallback and Path(fallback).exists():
        return to_posix(fallback)
    for hit in sorted(Path(".").glob(pattern)):
        return to_posix(str(hit))
    return None


def check_gate_compliance(target: WorkflowDocument) -> GateCheckResult:
    """target の直前ゲートをチェックして GateCheckResult を返す。"""
    violations: List[WorkflowDocument] = []
    missing: List[WorkflowDocument] = []
    naming_violations: List[WorkflowDocument] = []

    for gate_id in target.idx.preceding_gates():
        gate_doc = WorkflowDocument(scope=target.scope, idx=gate_id, path=None)
        expected = gate_doc._expected_path()

        if Path(expected).exists():
            gate_doc.path = expected
            if not gate_doc.approved():
                violations.append(gate_doc)
        else:
            # 期待パスが存在しない → glob で別のファイルを探す
            found = _find_gate_file(target.scope, gate_id)
            if found:
                # 命名規則違反（別名で存在）
                gate_doc.path = found
                naming_violations.append(gate_doc)
            else:
                missing.append(gate_doc)

    blocked = bool(violations or missing or naming_violations)
    return GateCheckResult(
        target=target,
        blocked=blocked,
        violations=violations,
        missing=missing,
        naming_violations=naming_violations,
    )


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


# ---------------------------------------------------------------------------
# main() phase helpers
# ---------------------------------------------------------------------------

def _parse_input() -> tuple[PreToolUsePayload, argparse.Namespace]:
    """Parse CLI arguments and stdin payload."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-path", default=None)
    args = ap.parse_args()
    raw = read_payload()
    event = parse_payload(raw)
    if not isinstance(event, PreToolUsePayload):
        event = PreToolUsePayload.from_dict(raw)
    DEBUG.log("input", tool_name=event.tool_name)
    return event, args


def _collect_targets(event: PreToolUsePayload, args: argparse.Namespace) -> List[str]:    
    """Collect and deduplicate target paths from tool_input and CLI/env fallback.

    Returns a deduplicated list of forward-slash-normalised paths.
    """
    raw_paths = get_written_paths(event.tool_name, event.tool_input) if event.tool_name else []
    targets = list(raw_paths)
    fallback = resolve_target_path(args.target_path)
    if fallback:
        targets.append(fallback)
    return dedup_paths(targets)


def _evaluate_targets(targets: List[str], args: argparse.Namespace) -> tuple[bool, List[GateCheckResult]]:
    """各書き込みターゲットに対してゲートチェックを実行する。"""
    results: List[GateCheckResult] = []
    blocked = False
    for path in targets:
        target = parse_write_target(path)
        if not target:
            continue
        result = check_gate_compliance(target)
        results.append(result)
        blocked = blocked or result.blocked
    return blocked, results


def _build_deny_reason(results: List[GateCheckResult]) -> str:
    """ブロック理由を人間が読める文字列で返す。"""
    reasons: List[str] = []
    for r in results:
        if not r.blocked:
            continue
        for v in r.violations:
            reasons.append(f"未承認: {v.path} (status 未承認)")
        for m in r.missing:
            reasons.append(f"ゲート未存在: {m._expected_path()}")
        for n in r.naming_violations:
            reasons.append(f"命名規則違反: {n.path} (期待: {n._expected_path()})")
    return "\n".join(reasons) or "フェーズゲート要件を満たしていません"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        # 1. 入力パース
        event, args = _parse_input()
        # 2. Skip判定
        # Only gate-check write tools; read operations are always allowed.
        if event.tool_name and not is_write_tool(event.tool_name):
            DEBUG.log("skip", reason="non-write tool")
            return
        # 3. ターゲット収集
        targets = _collect_targets(event, args)
        if not targets:
            return
        # 4. フェーズゲート評価
        blocked, results = _evaluate_targets(targets, args)
        if not results:
            return
        DEBUG.log("done", blocked=blocked, checked=len(results))
        # 5. result処理
        if blocked:
            sys.exit(event.deny(_build_deny_reason(results)))
    except SystemExit:
        raise
    except Exception as exc:
        DEBUG.log("error", exc=str(exc))


if __name__ == "__main__":
    main()
