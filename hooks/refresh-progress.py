#!/usr/bin/env python3
"""Claude Code PostToolUse hook (Edit|Write|MultiEdit).

Keeps the progress dashboard current. After Claude edits docs/sdlc/<slug>/STATUS.md,
it rewrites that workspace's progress.html, and the all-workspaces
docs/sdlc/progress.html, with scripts/progress.py. It only refreshes pages that
already exist: /react-webapp:progress (or progress.py) creates the first one, so
projects that never asked for a dashboard get no new files. It prints nothing
and never blocks.

Registered by the react-webapp plugin in hooks/hooks.json.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def main():
    try:
        path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
    except ValueError:
        return 0
    match = re.search(r"^(.*)/docs/sdlc/([^/]+)/STATUS\.md$", path or "")
    if not match:
        return 0
    project, workspace = Path(match.group(1)), Path(match.group(1), "docs/sdlc", match.group(2))
    pages = [(workspace / "progress.html", workspace), (project / "docs/sdlc/progress.html", None)]
    if not any(page.is_file() for page, _ in pages):
        return 0
    from progress import build
    for page, scope in pages:
        if page.is_file():
            build(project, scope)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BaseException as error:  # SystemExit included: a dashboard problem never gets in the way of an edit
        print(f"refresh-progress hook error (ignored): {error}", file=sys.stderr)
        sys.exit(0)
