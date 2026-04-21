"""Per-script debug flag and logging.

Each script has its own debug flag file and log file under .github/scripts/:
  Flag : <script_key>.debug       (create to enable)
  Log  : <script_key>.debug.log   (auto-created when debug is on)

script_key is derived from the _S identifier:
  "R-1:resolve-cascade-scope" → "resolve_cascade_scope"
"""

import os, json
from datetime import datetime

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _script_key(script):
    """Extract file-safe key from script identifier."""
    """R-1:resolve-cascade-scope" → "resolve_cascade_scope"""
    s = script.split(":", 1)[-1] if ":" in script else script
    return s.replace("-", "_")


def is_debug(script):
    """Check if debug mode is enabled for the given script."""
    key = _script_key(script)
    return os.path.exists(os.path.join(_SCRIPTS_DIR, f"{key}.debug"))


def debug_log(script, msg, **kw):
    """Write a timestamped debug log entry to the script-specific log file."""
    key = _script_key(script)
    if not os.path.exists(os.path.join(_SCRIPTS_DIR, f"{key}.debug")):
        return
    log_path = os.path.join(_SCRIPTS_DIR, f"{key}.debug.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{script}] {msg}"
    if kw:
        line += " | " + json.dumps(kw, ensure_ascii=False, default=str)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")
