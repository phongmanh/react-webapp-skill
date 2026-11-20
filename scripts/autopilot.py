#!/usr/bin/env python3
"""Autopilot for the react-webapp-sdlc skill: one fresh headless Claude session per plan item.

Runs `claude -p` in a loop. Each session does the next open row of the newest
"## Phase N plan" in docs/sdlc/<slug>/STATUS.md and rewrites the "## Handoff";
the plugin's session-context.py SessionStart hook hands that state to the next
session. Between sessions this script re-reads STATUS.md and stops when a human
is needed:
  - the Handoff's "Waiting on user" is anything but "nothing" (gate sign-off,
    a decision, a CR approval);
  - the next plan row is Blocked;
  - Phase 4 runs with code review mode "Approve before writing";
  - a session failed, made no change to STATUS.md, or ended with
    "AUTOPILOT-RESULT: stop <reason>";
  - --max-sessions or --budget-usd is reached.

Autopilot never records gate decisions, never pushes and never opens PRs.
The skill's "## Autopilot" section has the rules each session follows.

Usage, from the target project's root:
    python3 <plugin>/scripts/autopilot.py [--workspace docs/sdlc/<slug>] [--dry-run]
"""
import argparse
import datetime
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from sdlc_status import (  # noqa: E402
    detect_skill, field, handoff_field, newest_plan, next_plan_row, phase_number, plan_rows, workspaces,
)

SKILL = "react-webapp-sdlc"
RESULT_LINE = re.compile(r"^AUTOPILOT-RESULT:\s*(continue|stop)\b\s*(.*)$", re.IGNORECASE)
NOTHING = ("nothing", "none", "—", "-", "n/a")

ALLOWED_TOOLS = [
    "Skill", "Read", "Edit", "Write", "Glob", "Grep",
    "Bash(git status*)", "Bash(git diff*)", "Bash(git log*)", "Bash(git branch*)",
    "Bash(git switch *)", "Bash(git checkout -b *)", "Bash(git add *)", "Bash(git commit *)",
    "Bash(npm run *)", "Bash(npm ci)", "Bash(npm install)", "Bash(npm install *)", "Bash(npm ls *)",
    "Bash(npm audit*)", "Bash(npm create vite@latest *)", "Bash(npx playwright install *)",
    "Bash(node *)", "Bash(mkdir *)", "Bash(cp -Rn *)", "Bash(rm -rf .scaffold)",
]
DISALLOWED_TOOLS = [
    "Bash(git push*)", "Bash(git reset --hard*)", "Bash(git rebase*)", "Bash(git merge*)",
    "Bash(gh *)", "AskUserQuestion",
]

SYSTEM_PROMPT = (
    "AUTOPILOT MODE. No human is watching this session and nobody can answer questions. "
    "Follow the '## Autopilot' section of the SDLC skill. Do exactly one plan item, then the skill's "
    "End-of-session step (update the deliverable, the plan row and the ## Handoff). Never ask questions; "
    "anything only the owner can decide becomes an Open item, the plan row becomes 'Blocked: <reason>' and "
    "the Handoff's 'Waiting on user' names it. Never record a gate decision, never edit a baselined "
    "deliverable, never push. The last line of your reply must be exactly 'AUTOPILOT-RESULT: continue' "
    "or 'AUTOPILOT-RESULT: stop <reason>'."
)


COLORS = {"blue": "34", "green": "32", "amber": "33", "red": "31", "dim": "2"}


def paint(text, color):
    """Colors text for a terminal; plain when piped or when NO_COLOR is set."""
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return text
    return f"\033[{COLORS[color]}m{text}\033[0m"


def refresh_dashboard(project, workspace):
    """Rewrites the workspace's progress.html (scripts/progress.py). Best effort: returns its path or None."""
    try:
        from progress import build
        return build(project, workspace.relative_to(project))
    except Exception as error:  # SystemExit included: a dashboard problem never stops autopilot
        print(paint(f"  (progress dashboard not updated: {error})", "dim"), flush=True)
        return None


class Stop(Exception):
    """Autopilot stops. failed=True means something went wrong rather than a human being needed."""

    def __init__(self, reason, failed=False):
        super().__init__(reason)
        self.reason = reason
        self.failed = failed


def is_set(value):
    """False for empty values and template placeholders such as '<decision, or "nothing">'."""
    return bool(value) and not value.startswith("<")


def find_workspace(project, workspace):
    if workspace:
        path = (project / workspace).resolve()
        if not (path / "STATUS.md").is_file():
            raise Stop(f"No STATUS.md in {workspace}.", failed=True)
        return path
    found = workspaces(project)
    if len(found) != 1:
        names = ", ".join(str(path.relative_to(project)) for path in found) or "none"
        raise Stop(f"Pass --workspace: expected one docs/sdlc/*/STATUS.md, found {names}.", failed=True)
    return found[0]


def check_ready(text):
    """Raises Stop unless the interactive setup (scope and a first phase plan) is done."""
    plan = newest_plan(text)
    if plan is None or not any(is_set(row[1]) for row in plan_rows(plan[1])):
        raise Stop(
            "STATUS.md has no phase plan with real rows yet. Run the skill interactively first: "
            "scope, then the current phase's plan.",
            failed=True,
        )


def check_can_continue(text):
    """Raises Stop when the next step needs a human."""
    waiting = handoff_field(text, "Waiting on user")
    if is_set(waiting) and not waiting.lower().startswith(NOTHING):
        raise Stop(f"Waiting on user: {waiting}")
    row = next_plan_row(text)
    if row and row["status"].lower().startswith("blocked"):
        raise Stop(f"{row['plan']} #{row['number']} ({row['work']}) is {row['status']}")
    if phase_number(text) == 4 and "approve before" in field(text, "Code review mode").lower():
        raise Stop(
            "Phase 4 with code review mode 'Approve before writing' needs you for every PR. Switch STATUS.md "
            "to 'Review after writing' to use autopilot, or continue interactively."
        )


def session_prompt(skill, workspace_rel, row):
    head = f"Use the react-webapp-skill:{skill} skill in AUTOPILOT mode. Workspace: {workspace_rel}/."
    if row:
        return (
            f"{head} Do {row['plan']} #{row['number']}: {row['work']} - only this item - "
            "then the End-of-session step."
        )
    return (
        f"{head} The newest phase plan has no open row. Follow the Autopilot rule for an empty plan: if the "
        "gate log approves the current phase's gate, start the next phase and write its plan; otherwise run "
        "the gate review and set the Handoff's 'Waiting on user' to the sign-off."
    )


def build_command(args, prompt, budget_left):
    command = [
        args.claude_bin, "-p", prompt,
        "--output-format", "json",
        "--permission-mode", args.permission_mode,
        "--append-system-prompt", SYSTEM_PROMPT,
        "--allowedTools", *ALLOWED_TOOLS,
        "--disallowedTools", *DISALLOWED_TOOLS,
    ]
    if getattr(args, "model", None):
        command += ["--model", args.model]
    if getattr(args, "effort", None):
        command += ["--effort", args.effort]
    if budget_left is not None:
        command += ["--max-budget-usd", f"{budget_left:.2f}"]
    return command


def usage_summary(output):
    """Token counts of one session from claude's JSON result, for the log (missing fields are left out)."""
    usage = output.get("usage") or {}
    summary = {key: usage[key] for key in (
        "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens",
    ) if isinstance(usage.get(key), int)}
    if isinstance(output.get("num_turns"), int):
        summary["turns"] = output["num_turns"]
    return summary


def run_session(command, project, timeout_minutes):
    """Runs one session; returns (result text, cost, session id, token usage). Raises Stop on failure."""
    try:
        done = subprocess.run(
            command, cwd=project, capture_output=True, text=True, timeout=timeout_minutes * 60,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        raise Stop(f"The session ran longer than {timeout_minutes} minutes.", failed=True)
    except FileNotFoundError:
        raise Stop(f"Can't run {command[0]!r}; is Claude Code installed and on PATH?", failed=True)
    try:
        output = json.loads(done.stdout)
    except ValueError:
        output = None
    if done.returncode != 0 or not isinstance(output, dict):
        detail = (done.stderr or done.stdout).strip()[-500:]
        raise Stop(f"claude exited with code {done.returncode}: {detail}", failed=True)
    result = str(output.get("result") or "")
    cost = float(output.get("total_cost_usd") or 0)
    session_id = output.get("session_id", "")
    if output.get("is_error"):
        raise Stop(f"The session ended with an error ({output.get('subtype', 'error')}): {result[-500:]}",
                   failed=True)
    return result, cost, session_id, usage_summary(output)


def result_marker(result):
    """('continue' | 'stop' | None, reason) from the reply's last non-blank line."""
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    match = RESULT_LINE.match(lines[-1]) if lines else None
    return (match.group(1).lower(), match.group(2).strip()) if match else (None, "")


def log(log_file, **entry):
    log_file.parent.mkdir(parents=True, exist_ok=True)
    entry = {"time": datetime.datetime.now().isoformat(timespec="seconds"), **entry}
    with log_file.open("a", encoding="utf-8") as out:
        out.write(json.dumps(entry) + "\n")


def autopilot(args):
    project = Path(args.project).resolve()
    workspace = find_workspace(project, args.workspace)
    workspace_rel = workspace.relative_to(project)
    status_file = workspace / "STATUS.md"
    log_file = project / ".claude/autopilot" / f"{workspace.name}.jsonl"
    text = status_file.read_text(encoding="utf-8")
    skill = args.skill or detect_skill(text)
    check_ready(text)

    spent, sessions, dashboard = 0.0, 0, None
    try:
        while True:
            check_can_continue(text)
            if sessions >= args.max_sessions:
                raise Stop(f"Reached --max-sessions {args.max_sessions}.")
            budget_left = None if args.budget_usd is None else args.budget_usd - spent
            if budget_left is not None and budget_left <= 0:
                raise Stop(f"Reached --budget-usd {args.budget_usd:.2f} (spent {spent:.2f}).")

            row = next_plan_row(text)
            item = f"{row['plan']} #{row['number']}: {row['work']}" if row else "advance to the next phase"
            command = build_command(args, session_prompt(skill, workspace_rel, row), budget_left)
            if args.dry_run:
                print(f"[dry run] next session: {item}\n{shlex.join(command)}")
                raise Stop("Dry run: no session started.")

            sessions += 1
            print(paint(f"▶ Session {sessions}/{args.max_sessions} · {item}", "blue"), flush=True)
            try:
                result, cost, session_id, usage = run_session(command, project, args.session_timeout)
            except Stop as stop:
                log(log_file, session=sessions, item=item, outcome="failed", reason=stop.reason)
                raise
            spent += cost
            marker, reason = result_marker(result)
            new_text = status_file.read_text(encoding="utf-8")
            log(log_file, session=sessions, session_id=session_id, item=item, cost_usd=round(cost, 4),
                marker=marker, reason=reason, status_changed=new_text != text, usage=usage)
            print(paint(f"  ✔ done · ${cost:.2f} · session {session_id}{': ' + reason if reason else ''}", "green"),
                  flush=True)
            if args.dashboard:
                dashboard = refresh_dashboard(project, workspace)

            if new_text == text:
                raise Stop(f"Session {sessions} didn't change STATUS.md; stopping to avoid a loop.", failed=True)
            text = new_text
            if marker == "stop":
                raise Stop(reason or "The session asked to stop.")
    finally:
        if dashboard:
            print(paint(f"Progress dashboard: {dashboard}", "dim"), flush=True)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Run the react-webapp-sdlc skill unattended, one session per plan item.")
    parser.add_argument("--project", default=".", help="the target project's root (default: current directory)")
    parser.add_argument("--workspace", help="docs/sdlc/<slug>, relative to the project (default: the only one)")
    parser.add_argument("--skill", choices=(SKILL,), help="default: react-webapp-sdlc")
    parser.add_argument("--model", help="model for each session (default: Claude Code's)")
    parser.add_argument("--effort", choices=("low", "medium", "high", "xhigh", "max"),
                        help="effort for each session (default: Claude Code's)")
    parser.add_argument("--max-sessions", type=int, default=20)
    parser.add_argument("--budget-usd", type=float, help="stop once the sessions together have cost this much")
    parser.add_argument("--session-timeout", type=int, default=90, help="minutes per session (default: 90)")
    parser.add_argument("--permission-mode", default="acceptEdits",
                        help="passed to claude (default: acceptEdits; tools outside the allow list are denied)")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--dry-run", action="store_true", help="print the next session's command and stop")
    parser.add_argument("--no-dashboard", dest="dashboard", action="store_false",
                        help="don't refresh progress.html (scripts/progress.py) after each session")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        autopilot(args)
    except Stop as stop:
        print(paint(f"■ Autopilot stopped: {stop.reason}", "red" if stop.failed else "amber"))
        if not stop.failed and not args.dry_run:
            print("Do what it needs in an interactive session, then run autopilot again.")
        return 1 if stop.failed else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
