"""File I/O and JSON output helpers."""

import os, sys, json


def read_text(path):
    """Read a text file and return its content, or None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return None


def write_text(path, text):
    """Write text to a file, creating parent directories as needed."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def norm(p):
    """Normalise path to forward-slash form."""
    return str(p).replace("\\", "/")


def out_json(data):
    """Print structured JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def out_err(msg, code=1):
    """Print error JSON to stdout and exit."""
    out_json({"success": False, "error": msg})
    sys.exit(code)
