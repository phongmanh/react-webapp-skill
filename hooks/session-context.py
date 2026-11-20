#!/usr/bin/env python3
"""Claude Code SessionStart hook.

Tells Claude where each SDLC workspace (docs/sdlc/<slug>/STATUS.md) stands, so
a new, cleared, resumed or compacted session continues the right work instead
of re-reading everything. It prints the current phase, the next open item of
the current phase plan and the "## Handoff" section, which the SDLC skill
rewrites at the end of every session. Stdout becomes session context.

Registered by the react-webapp plugin in hooks/hooks.json.
"""
import json
import os
import sys
from pathlib import Path

from sdlc_status import field, handoff, next_plan_item

HANDOFF_MAX_LINES = 30
HANDOFF_MAX_CHARS = 3000


def describe(project_dir, status_file):
    text = status_file.read_text(encoding="utf-8")
    lines = [f"SDLC workspace {status_file.parent.relative_to(project_dir)}/ (this is STATUS.md's summary; "
             "read other sections of it only when the task needs them):"]
    for name in ("Current phase", "Code review mode", "Last updated"):
        value = field(text, name)
        if value:
            lines.append(f"- {name}: {value}")
    item = next_plan_item(text)
    if item:
        lines.append(f"- Next plan item: {item}")
    note = handoff(text, HANDOFF_MAX_LINES, HANDOFF_MAX_CHARS)
    if note:
        lines += [
            "",
            'Handoff from the last session (STATUS.md "## Handoff"). Start from its next action, load only '
            "what it lists, and rewrite it before this session ends (the SDLC skill's End of session step):",
            note,
        ]
    return "\n".join(lines)


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())
    status_files = sorted(project_dir.glob("docs/sdlc/*/STATUS.md"))
    if not status_files:
        return 0
    blocks = [describe(project_dir, status_file) for status_file in status_files]
    if os.environ.get("SDLC_GATE", "").lower() == "off":
        blocks.append(
            "SDLC_GATE=off: the user has switched off the baseline gate for this session. Baselined documents "
            "still change only through an approved CR; say so when you edit one."
        )
    print("\n\n".join(blocks))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:  # never wedge a session on a hook bug
        print(f"session-context hook error (ignored): {error}", file=sys.stderr)
        sys.exit(0)
