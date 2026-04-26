#!/usr/bin/env python3
"""Shared debug logging helpers for hook scripts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Optional, Tuple


def build_debug_paths(script_dir: Path, script_name: str) -> Tuple[Path, Path]:
    """Return (flag_path, log_path) for a hook script name."""
    return (
        script_dir / f"{script_name}.debug",
        script_dir / f"{script_name}.debug.log",
    )


def is_debug_enabled(flag_path: Path) -> bool:
    """Debug mode is enabled when the flag file exists."""
    return flag_path.exists()


def default_payload_formatter(payload: Dict[str, object]) -> str:
    if not payload:
        return ""
    return " | " + json.dumps(payload, ensure_ascii=False, default=str)


def append_debug_line(log_path: Path, line: str) -> None:
    with log_path.open("a", encoding="utf-8") as f:
        f.write(f"{line}\n")


class HookDebugLogger:
    """Small utility that handles debug flag checks and log writes."""

    def __init__(
        self,
        script_dir: Path,
        script_name: str,
        payload_formatter: Optional[Callable[[Dict[str, object]], str]] = None,
    ) -> None:
        self.flag_path, self.log_path = build_debug_paths(script_dir, script_name)
        self._payload_formatter = payload_formatter or default_payload_formatter

    def enabled(self) -> bool:
        return is_debug_enabled(self.flag_path)

    def log(self, message: str, **kwargs: object) -> None:
        if not self.enabled():
            return
        payload = self._payload_formatter(kwargs) if kwargs else ""
        append_debug_line(self.log_path, f"{message}{payload}")
