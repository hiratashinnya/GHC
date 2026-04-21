"""YAML frontmatter parsing and updating."""

import re, json
from pathlib import Path

from ._io import read_text, write_text, norm


def _scalar(raw):
    """Parse a single YAML scalar value."""
    s = raw.strip()
    if not s:
        return None
    if len(s) >= 2:
        if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"):
            return s[1:-1]
    if "#" in s:
        s = s[:s.index("#")].strip()
    if not s or s in ("null", "~"):
        return None
    if s in ("true", "True", "yes"):
        return True
    if s in ("false", "False", "no"):
        return False
    for conv in (int, float):
        try:
            return conv(s)
        except ValueError:
            pass
    return s


def parse_fm(path):
    """Parse YAML frontmatter from a Markdown file → dict | None."""
    text = read_text(path)
    if text is None:
        return None
    m = re.match(r"^---[ \t]*\r?\n(.*?)\r?\n---", text, re.DOTALL)
    if not m:
        return None
    result = {}
    lines = m.group(1).split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s or s.startswith("#"):
            i += 1
            continue
        if ln[0:1].isspace():
            i += 1
            continue
        if ":" not in s:
            i += 1
            continue
        ci = s.index(":")
        key = s[:ci].strip()
        rest = s[ci + 1:].strip()
        if rest.startswith("["):
            try:
                result[key] = json.loads(rest)
            except json.JSONDecodeError:
                result[key] = rest
            i += 1
        elif rest == "":
            items = []
            i += 1
            while i < len(lines) and lines[i][:1] in (" ", "\t"):
                sl = lines[i].strip()
                if sl.startswith("- "):
                    iv = sl[2:].strip()
                    if ":" in iv:
                        k2, v2 = iv.split(":", 1)
                        items.append({k2.strip(): _scalar(v2)})
                    else:
                        items.append(_scalar(iv))
                elif ":" in sl and items and isinstance(items[-1], dict):
                    k2, v2 = sl.split(":", 1)
                    items[-1][k2.strip()] = _scalar(v2)
                i += 1
            result[key] = items
        else:
            result[key] = _scalar(rest)
            i += 1
    return result


def scan_fm(directory, recursive=True):
    """Scan .md files → list[dict] each with '_path' key."""
    d = Path(directory)
    if not d.exists():
        return []
    pat = "**/*.md" if recursive else "*.md"
    out = []
    for p in sorted(d.glob(pat)):
        if p.name == "dashboard.md":
            continue
        fm = parse_fm(str(p))
        if fm is not None:
            fm["_path"] = norm(p)
            out.append(fm)
    return out


def _ser(v):
    """Serialize a Python value to YAML inline form."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[]" if not v else json.dumps(v, ensure_ascii=False)
    return str(v)


def update_fm(path, updates):
    """Update scalar / inline-list fields in frontmatter.  Returns True on success."""
    text = read_text(path)
    if text is None:
        return False
    m = re.match(r"^(---[ \t]*\r?\n)(.*?)(\r?\n---)", text, re.DOTALL)
    if not m:
        return False
    fm_lines = m.group(2).split("\n")
    body = text[m.end():]
    done = set()
    out = []
    skip = False
    for ln in fm_lines:
        if skip:
            if ln[:1] in (" ", "\t"):
                continue
            skip = False
        s = ln.strip()
        key = None
        if s and not ln[0:1].isspace() and ":" in s:
            key = s[:s.index(":")].strip()
        if key and key in updates:
            out.append(f"{key}: {_ser(updates[key])}")
            done.add(key)
            rest = s[s.index(":") + 1:].strip()
            if rest == "":
                skip = True
        else:
            out.append(ln)
    for k, v in updates.items():
        if k not in done:
            out.append(f"{k}: {_ser(v)}")
    new = m.group(1) + "\n".join(out) + m.group(3) + body
    write_text(path, new)
    return True


def add_tags(path, new_tags):
    """Append tags to the tags array without duplicates."""
    fm = parse_fm(path)
    if fm is None:
        return False
    cur = fm.get("tags") or []
    merged = list(cur) + [t for t in new_tags if t not in cur]
    return update_fm(path, {"tags": merged})


def append_changelog(path, date_str, reason, version="", author=""):
    """Append a row to the 変更履歴 table (create section if absent)."""
    text = read_text(path)
    if text is None:
        return False
    row = f"| {date_str} | {version} | {reason} | {author} |"
    m2 = re.search(r"(## 変更履歴[^\n]*\n(?:\|[^\n]*\n)*)", text)
    if m2:
        pos = m2.end()
        text = text[:pos] + row + "\n" + text[pos:]
    else:
        text = (
            text.rstrip()
            + f"\n\n## 変更履歴\n\n| 日付 | バージョン | 変更内容 | 担当者 |\n|------|-----------|---------|------|\n{row}\n"
        )
    write_text(path, text)
    return True
