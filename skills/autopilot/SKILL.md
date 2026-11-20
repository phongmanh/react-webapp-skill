---
name: autopilot
description: Runs the react-webapp SDLC workflow unattended - a driver script starts one fresh headless Claude session per row of the current phase plan in docs/sdlc/<slug>/STATUS.md, and stops by itself at every gate sign-off, blocked row or decision only the owner can make. Use when the user asks to run autopilot, run the plan unattended or in the background, or keep going without them, for work run with the react-webapp skill.
argument-hint: "[workspace slug] [--budget-usd N] [--max-sessions N]"
allowed-tools: Bash(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py" *)
---
# Autopilot

Starts the unattended mode of the [react-webapp](../react-webapp/SKILL.md) skill. A driver script runs a fresh headless session (`claude -p`) for each row of the current `## Phase <n> plan`, and the SessionStart hook hands each one the last handoff. What each session does is in that skill's `## Autopilot` section. **Gates still stop:** autopilot never records a gate decision.

Arguments: `$ARGUMENTS`

## Steps
1. **Pick the workspace.** It's `docs/sdlc/<slug>/` in the project root. Use the slug from the arguments. With no slug and more than one workspace, ask which one. With none, explain that `/react-webapp` creates it, and stop.
2. **Check it's ready.** Read the top of its `STATUS.md`. Scope (step 3 of the react-webapp skill) must be done, and STATUS.md must have a `## Phase <n> plan` with real rows. If not, do those first, with the user, in the react-webapp skill.
3. **Phase 4 only:** **Code review mode** must be *Review after writing*. *Approve before writing* needs the owner for every PR, so autopilot refuses it. Offer to switch it, or continue interactively.
4. **Dry run.** From the project root, run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/autopilot.py" --workspace docs/sdlc/<slug> --dry-run`, passing on any options from the arguments. Show the user the next item and the command.
5. **Run it** with the same command minus `--dry-run`, using Bash `run_in_background`. Options: `--model` and `--effort` (default: Claude Code's), `--max-sessions` (default 20), `--budget-usd`, `--session-timeout` (minutes, default 90), `--no-dashboard`.
6. **Tell the user:**
   - it stops by itself when it needs them (a gate sign-off, a decision, a blocked row, a failed session, or a cap);
   - `TaskStop` (or Ctrl-C) stops it early;
   - each session is logged in `.claude/autopilot/<slug>.jsonl`, and `/react-webapp:progress` shows where it stands.

When it finishes, read its last lines and say why it stopped and what the user needs to do next.
