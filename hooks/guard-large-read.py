#!/usr/bin/env python3
"""Claude Code PreToolUse hook (Read).

Refuses a whole-file Read of a file over MAX_BYTES under docs/sdlc/ and returns
its outline (line: heading), so the session reads only the sections it needs.
Every token read stays in the context and is re-sent on every later call, so a
whole design or contract read early in a session is paid many times over.
A Read with offset or limit always passes.

Registered by the react-webapp-skill plugin in hooks/hooks.json.
"""
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 24_000
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


def main():
    try:
        tool_input = json.load(sys.stdin).get("tool_input", {})
    except ValueError:
        return 0
    if tool_input.get("offset") or tool_input.get("limit"):
        return 0
    path = Path(tool_input.get("file_path", ""))
    if "/docs/sdlc/" not in path.as_posix() or not path.is_file():
        return 0
    size = path.stat().st_size
    if size <= MAX_BYTES:
        return 0
    reason = (
        f"{path.name} is {size // 1000} KB, too large to read whole (react-webapp-skill). Read only the sections "
        f"this task needs, with offset and limit. Outline (line: heading):\n{outline(path)}"
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
