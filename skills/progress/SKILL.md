---
name: progress
description: Shows where an SDLC workspace stands, as a short summary plus a colorful dashboard page (progress.html) built from docs/sdlc/<slug>/STATUS.md - the phase timeline, gates, the current plan, deliverables, risks and what's waiting on the user. Use when the user asks for the progress, status, dashboard or "where are we" of work run with the react-webapp-sdlc skill.
argument-hint: "[workspace slug]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/progress.py" *)
---
# Progress

The dashboard script already ran for this request. Its output:

!`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/progress.py" $ARGUMENTS --open 2>&1 || true`

Reply in a few short lines, based only on that output:
- Where the work stands: the phase, plan progress and the next plan item.
- Anything **Waiting on you**, first and in bold, when it isn't "nothing".
- The dashboard's path. It has opened in the browser, and from now on it refreshes itself whenever STATUS.md changes.

If the output says there's no workspace, explain that the dashboard reads `docs/sdlc/<slug>/STATUS.md`, which `/react-webapp-skill:react-webapp-sdlc` creates at the start of the work. If it lists the workspaces because the name didn't match, ask which one to show.

To run it again yourself (e.g. after the user names a workspace), use `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/progress.py" <slug> --open`. The script also takes `--phases "A,B,C"` or `--skill-dir <skill folder>` to name the phases of a workspace that another skill owns.
