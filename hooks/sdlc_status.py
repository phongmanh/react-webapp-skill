"""Reads the parts of an SDLC STATUS.md that the hooks and the autopilot driver need.

Shared by hooks/session-context.py and scripts/autopilot.py. Standard library only.
"""
import re

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
SECTION = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
PLAN_HEADING = re.compile(r"Phase (\d+) plan")


def cells(row):
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def sections(text):
    """Maps each "## " heading to the text under it, up to the next "## " heading."""
    matches = list(SECTION.finditer(text))
    return {
        m.group(1): text[m.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)]
        for i, m in enumerate(matches)
    }


def field(text, name):
    """The value of a "| Field | Value |" row in the header table, or ''."""
    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            row = cells(line)
            if len(row) >= 2 and row[0].lower() == name.lower():
                return row[1]
    return ""


def newest_plan(text):
    """(heading, body) of the "## Phase N plan" with the highest N, or None."""
    plans = [(heading, body) for heading, body in sections(text).items() if PLAN_HEADING.fullmatch(heading)]
    if not plans:
        return None
    return max(plans, key=lambda plan: int(PLAN_HEADING.fullmatch(plan[0]).group(1)))


def plan_rows(body):
    """The data rows of a plan table, skipping the header and the separator."""
    rows = [cells(line) for line in body.splitlines() if line.lstrip().startswith("|")]
    return [row for row in rows[2:] if len(row) >= 2]


def next_plan_row(text):
    """The first row of the newest plan whose status isn't Done, as a dict, or None.

    Keys: plan (the heading), number, work, needs (the "Needs from the owner" cell, or '') and status.
    """
    plan = newest_plan(text)
    if plan is None:
        return None
    heading, body = plan
    for row in plan_rows(body):
        if not row[-1].lower().startswith("done"):
            return {
                "plan": heading,
                "number": row[0],
                "work": row[1],
                "needs": row[-2] if len(row) >= 4 else "",
                "status": row[-1],
            }
    return None


def next_plan_item(text):
    """The next open plan row as "Phase N plan #n: work (status)", or ''."""
    row = next_plan_row(text)
    return f"{row['plan']} #{row['number']}: {row['work']} ({row['status']})" if row else ""


def handoff_lines(text):
    """The non-blank lines of the "## Handoff" section, without comments."""
    body = sections(text).get("Handoff", "")
    return [line for line in COMMENT.sub("", body).splitlines() if line.strip()]


def handoff(text, max_lines, max_chars):
    """The "## Handoff" section without comments or blank lines, capped, or ''."""
    lines = handoff_lines(text)
    capped = "\n".join(lines[:max_lines])
    truncated = len(lines) > max_lines or len(capped) > max_chars
    return capped[:max_chars] + ("\n… (truncated: keep the Handoff section short)" if truncated else "")


def handoff_field(text, name):
    """The value of a "- **<name>:** value" line in the Handoff section, or ''."""
    pattern = re.compile(r"^\s*[-*]\s*\*\*" + re.escape(name) + r":?\*\*:?\s*(.*)$", re.IGNORECASE)
    for line in handoff_lines(text):
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return ""


def workspaces(project):
    """The SDLC workspaces (docs/sdlc/<slug>/ folders with a STATUS.md) under a project, sorted."""
    return [status.parent for status in sorted(project.glob("docs/sdlc/*/STATUS.md"))]


def detect_skill(_text):
    """The skill that owns a STATUS.md. This plugin has one."""
    return "react-webapp-sdlc"


def phase_number(text):
    """The number that starts the "Current phase" field, or None."""
    match = re.match(r"\s*(\d+)", field(text, "Current phase"))
    return int(match.group(1)) if match else None


def table_rows(body):
    """The first table in a section body as dicts keyed by its header cells. Comments are skipped."""
    lines = []
    for line in COMMENT.sub("", body).splitlines():
        if line.lstrip().startswith("|"):
            lines.append(line)
        elif lines:
            break
    if len(lines) < 2:
        return []
    header = cells(lines[0])
    rows = []
    for line in lines[2:]:
        row = cells(line)
        rows.append({name: row[i] if i < len(row) else "" for i, name in enumerate(header)})
    return rows


def section_rows(text, heading):
    """table_rows() of the first "## " section whose heading starts with `heading` (any case)."""
    for name, body in sections(text).items():
        if name.lower().startswith(heading.lower()):
            return table_rows(body)
    return []


def column(row, prefix):
    """The value of the first column whose header starts with `prefix` (any case), or ''.

    Matching by prefix lets "Status" find "Status (Not started / Draft / In review / Approved)".
    """
    prefix = prefix.lower()
    for name, value in row.items():
        if name.lower().startswith(prefix):
            return value
    return ""


def plan_progress(text):
    """The newest phase plan as a dict, or None.

    Keys: heading, phase (its number), rows (table_rows, template placeholder rows dropped),
    done and total.
    """
    plan = newest_plan(text)
    if plan is None:
        return None
    heading, body = plan
    rows = [row for row in table_rows(body) if len(row) >= 2 and not list(row.values())[1].startswith("<")]
    done = sum(1 for row in rows if list(row.values())[-1].lower().startswith("done"))
    return {
        "heading": heading,
        "phase": int(PLAN_HEADING.fullmatch(heading).group(1)),
        "rows": rows,
        "done": done,
        "total": len(rows),
    }
