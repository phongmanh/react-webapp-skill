#!/usr/bin/env python3
"""Claude Code PreToolUse hook (Read).

Refuses a Read under docs/sdlc/ that would return more than MAX_BYTES - a whole
large file, or a range wide enough to cover most of one - and returns the
file's outline (line: heading), so the session reads only the sections it
needs. Every token read stays in the context and is re-sent on every later
call, so a whole design or contract read early in a session is paid many times
over.

Registered by the react-webapp plugin in hooks/hooks.json.
"""
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 24_000
DEFAULT_LIMIT = 2000  # lines the Read tool returns when no limit is given
MAX_OUTLINE = 120
MARKDOWN_HEADING = re.compile(r"^#{1,4} ")
YAML_KEY = re.compile(r"^ {0,4}[^\s#-][^:]*:\s*$")  # top-level keys, paths and schema names


def outline(path):
    pattern = MARKDOWN_HEADING if path.suffix == ".md" else YAML_KEY
    with path.open(encoding="utf-8", errors="replace") as text:
        rows = [f"{number}: {line.rstrip()[:100]}" for number, line in enumerate(text, 1) if pattern.match(line)]
    if len(rows) > MAX_OUTLINE:
        rows = rows[:MAX_OUTLINE] + [f"… {len(rows) - MAX_OUTLINE} more; use Grep for the rest"]
    return "\n".join(rows) or "(no headings found; use Grep to find the lines you need)"


def requested_bytes(path, offset, limit):
    """Bytes the Read would return: lines offset .. offset+limit-1 (1-based)."""
    first = max(int(offset or 1), 1)
    last = first + int(limit or DEFAULT_LIMIT) - 1
    total = 0
    with path.open("rb") as text:
        for number, line in enumerate(text, 1):
            if number > last:
                break
            if number >= first:
                total += len(line)
    return total


def main():
    try:
        tool_input = json.load(sys.stdin).get("tool_input", {})
    except ValueError:
        return 0
    path = Path(tool_input.get("file_path", ""))
    if "/docs/sdlc/" not in path.as_posix() or not path.is_file():
        return 0
    ranged = bool(tool_input.get("offset") or tool_input.get("limit"))
    size = requested_bytes(path, tool_input.get("offset"), tool_input.get("limit"))
    if size <= MAX_BYTES:
        return 0
    what = "That range" if ranged else path.name
    reason = (
        f"{what} is {size // 1000} KB, too large to read at once (react-webapp plugin; limit "
        f"{MAX_BYTES // 1000} KB per Read). Read only the sections this task needs, with offset and limit. "
        f"Outline of {path.name} (line: heading):\n{outline(path)}"
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # never wedge a session on a hook bug
        print(f"guard-large-read hook error (ignored): {error}", file=sys.stderr)
        sys.exit(0)
