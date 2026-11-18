#!/usr/bin/env python3
"""Progress dashboard: turns an SDLC STATUS.md into a colorful, self-contained HTML page.

It shows the phase timeline, the gate log, the newest "## Phase N plan", the
deliverables, the risks, open items and change requests, and the "## Handoff".
It reads the STATUS.md *shape*, not anything web-specific, so any skill whose
STATUS.md keeps these sections can use it; a missing section is left out.

Phase names come from, in order: --phases "A,B,C"; --skill-dir <skill> (its
phases/<n>-<name>.md files); the plugin's own skill that the STATUS.md belongs to;
otherwise "Phase <n>".

Usage, from anywhere inside the target project (or /react-webapp-skill:progress in Claude Code):
    python3 <plugin>/scripts/progress.py [<slug>] [--open]
It writes progress.html next to STATUS.md (or docs/sdlc/progress.html for several
workspaces), prints a short summary and the page's path. Once a page exists, the
plugin's refresh-progress.py hook keeps it current. Standard library only.
"""
import argparse
import datetime
import html
import re
import sys
import webbrowser
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN / "hooks"))
from sdlc_status import (  # noqa: E402
    column, detect_skill, field, handoff_field, handoff_lines, phase_number, plan_progress, section_rows,
    workspaces,
)

PALETTE = 7  # --p1 … --p7 in the CSS; phases beyond 7 reuse the colors in order
CODE = re.compile(r"`([^`]+)`")
PLACEHOLDER = re.compile(r"<[^>]+>|YYYY")
PHASE_FILE = re.compile(r"(\d+)-(.+)\.md$")
GATE_ID = re.compile(r"\s*(G\d+)\b\s*(.*)$", re.IGNORECASE)
EMPTY = ("", "—", "–", "-", "n/a", "none")
NOTHING = ("nothing", "none", "—", "-", "n/a")
LEVEL = {"l": 1, "m": 2, "h": 3}


# ---------- reading ----------

def filled(value):
    """False for empty cells, dashes and template placeholders such as '<name>' or 'YYYY-MM-DD'."""
    value = (value or "").strip()
    return value.lower() not in EMPTY and "<" not in value[:1] and "YYYY" not in value


def phase_color(number):
    return f"var(--p{(number - 1) % PALETTE + 1})"


def names_from_skill_dir(skill_dir):
    """{n: "Name"} from phases/<n>-<name>.md, e.g. 3-detailed-design.md -> "Detailed design"."""
    names = {}
    for path in sorted(Path(skill_dir, "phases").glob("*.md")):
        match = PHASE_FILE.match(path.name)
        if match:
            names[int(match.group(1))] = match.group(2).replace("-", " ").capitalize()
    return names


def phase_names(text, skill_dir=None, names=None):
    """{n: name} for every phase, numbered from 1."""
    if names:
        return {i + 1: name.strip() for i, name in enumerate(names) if name.strip()}
    if skill_dir is None:
        owners = [path.parent for path in sorted((PLUGIN / "skills").glob("*/phases"))]
        mentioned = [d for d in owners if re.search(rf"(?<![\w-]){re.escape(d.name)}(?![\w-])", text)]
        skill_dir = mentioned[0] if mentioned else PLUGIN / "skills" / detect_skill(text)
    found = names_from_skill_dir(skill_dir) if Path(skill_dir).is_dir() else {}
    if found:
        return found
    current = phase_number(text) or 1
    plan = plan_progress(text)
    count = max(current, plan["phase"] if plan else 1)
    names = {n: f"Phase {n}" for n in range(1, count + 1)}
    label = re.sub(r"^\s*\d+\s*", "", field(text, "Current phase")).split(":")[0].strip()
    if label:
        names[current] = label
    return names


def title_of(text, fallback):
    match = re.search(r"^#\s+(?:STATUS:\s*)?(.+?)\s*$", text, re.MULTILINE)
    name = match.group(1) if match else ""
    return name if filled(name) else fallback


def plan_tone(status):
    s = status.lower()
    if s.startswith("done"):
        return "ok", "Done"
    if s.startswith("blocked"):
        return "bad", "Blocked"
    if s.startswith(("in progress", "in review")):
        return "info", status
    return "idle", status or "Not started"


STAGES = (  # least to most mature: (word, chip tone, label)
    ("not started", "idle", "Not started"), ("draft", "warn", "Draft"), ("proposed", "info", "Proposed"),
    ("in review", "info", "In review"), ("approved", "ok", "Approved"),
)


def deliverable_status(status):
    """(tone, label, note) for a Deliverables status cell, or (None, '', note) when it names no stage.

    "Approved (G1, 2026-11-18)" -> ("ok", "Approved", "G1, 2026-11-18"). A cell that mixes stages without
    leading with one ("§1 Approved; §2 Draft") gets its least mature stage, with the whole cell as the note.
    """
    text = status.strip()
    lower = text.lower()
    for word, tone, label in STAGES:
        if lower.startswith(word):
            note = text[len(word):].strip(" :;,.-–—")
            if note.startswith("(") and note.endswith(")") and note.count("(") == 1:
                note = note[1:-1]
            return tone, label, note
    for word, tone, label in STAGES:
        if re.search(rf"\b{word}\b", lower):
            return tone, label, text
    return None, "", text


def gate_tone(decision):
    """(chip class, label, passed) for a gate log decision."""
    s = decision.lower()
    if not filled(decision):
        return "pending", "Pending", False
    if s.startswith("approved with"):
        return "warn", "With conditions", True
    if s.startswith("approved"):
        return "ok", "Approved", True
    if s.startswith("rejected"):
        return "bad", "Rejected", False
    if s.startswith("waived"):
        return "idle", "Waived", True
    return "idle", decision, False


def is_open(status, closed=("closed", "done", "resolved", "retired", "accepted", "implemented", "rejected")):
    return not status.lower().startswith(closed)


# ---------- rendering ----------

def esc(value, empty="—"):
    """Escapes a cell for HTML and turns `code` into mono text. Unfilled cells become a muted dash."""
    if not filled(value):
        return f'<span class="muted">{empty}</span>' if empty else ""
    return CODE.sub(r'<span class="mono">\1</span>', html.escape(value.replace("**", "").strip()))


def chip(tone, label):
    return f'<span class="chip {tone}">{esc(label, empty="")}</span>'


def gates(text):
    result = []
    for row in section_rows(text, "Gate log"):
        match = GATE_ID.match(column(row, "Gate"))
        if not match:
            continue
        number = int(re.sub(r"\D", "", match.group(1)))
        tone, label, passed = gate_tone(column(row, "Decision"))
        result.append({
            "id": match.group(1).upper(), "number": number, "name": match.group(2), "tone": tone,
            "label": label, "passed": passed, "date": column(row, "Date"), "approver": column(row, "Approver"),
            "conditions": column(row, "Conditions"), "tag": column(row, "Tag"),
        })
    for gate in result:  # the first undecided gate is the next one
        if gate["tone"] == "pending":
            gate["label"] = "Next"
            break
    return result


def render_stepper(names, current, gate_list, plan):
    gate_by_phase = {g["number"]: g for g in gate_list}
    count = len(names)
    spectrum, steps = [], []
    for n in sorted(names):
        state = "done" if current and n < current else "now" if n == current else "later"
        gate = gate_by_phase.get(n)
        if state == "done":
            sub = f'{gate["id"]} {gate["label"].lower()}' if gate and gate["tone"] != "pending" else "Done"
        elif state == "now":
            sub = "In progress"
            if plan and plan["phase"] == n and plan["total"]:
                sub += f' · {plan["done"]}/{plan["total"]}'
        else:
            sub = gate["id"] if gate else ""
        prev = f";--prev:{phase_color(n - 1)}" if n > 1 else ""
        node = "✓" if state == "done" else str(n)
        steps.append(
            f'<li class="step {state}" style="--c:{phase_color(n)}{prev}"><span class="node">{node}</span>'
            f'<span class="step-name">{esc(names[n])}</span><span class="step-sub">{esc(sub, empty="")}</span></li>'
        )
        later = "" if state != "later" else ' class="later"'
        spectrum.append(f'<span{later} style="background:{phase_color(n)}"></span>')
    columns = f"grid-template-columns:repeat({count},minmax(78px,1fr));min-width:{max(count * 80, 240)}px"
    return (
        f'<div class="spectrum" style="grid-template-columns:repeat({count},1fr)" aria-hidden="true">'
        f'{"".join(spectrum)}</div>'
        f'<div class="stepper-scroll"><ol class="stepper" style="{columns}">{"".join(steps)}</ol></div>'
    )


def render_kpis(names, current, plan, gate_list, risk_list):
    count = len(names)
    fraction = plan["done"] / plan["total"] if plan and plan["total"] and plan["phase"] == current else 0
    lifecycle = round(100 * min(1, max(0, ((current or 1) - 1 + fraction) / count)))
    tiles = [
        ("Lifecycle", f"{lifecycle}%", lifecycle,
         f"linear-gradient(90deg,{phase_color(1)},{phase_color(max(current or 1, 1))})"),
    ]
    if plan:
        pct = 100 * plan["done"] / plan["total"] if plan["total"] else 0
        tiles.append((plan["heading"], f'{plan["done"]}<small> / {plan["total"]} done</small>', pct,
                      phase_color(plan["phase"])))
    if gate_list:
        passed = sum(g["passed"] for g in gate_list)
        tiles.append(("Gates passed", f"{passed}<small> / {len(gate_list)}</small>",
                      100 * passed / len(gate_list), "var(--ok)"))
    open_risks = [r for r in risk_list if r["open"]]
    high = sum(1 for r in open_risks if r["score"] >= 5)
    if risk_list:
        tiles.append(("Open risks", f"{len(open_risks)}<small> · {high} high</small>",
                      100 * high / len(open_risks) if open_risks else 0, "var(--bad)"))
    out = [
        f'<div class="kpi"><span class="kpi-label">{esc(label)}</span><span class="kpi-value tnum">{value}</span>'
        f'<div class="kpi-bar"><i style="width:{bar:.1f}%;background:{color}"></i></div></div>'
        for label, value, bar, color in tiles
    ]
    return f'<section class="kpis" aria-label="Summary">{"".join(out)}</section>'


def render_plan(plan, uid):
    if not plan:
        return ""
    total, done = plan["total"], plan["done"]
    tones = [plan_tone(list(row.values())[-1])[0] for row in plan["rows"]]
    circumference = 2 * 3.14159 * 44
    dash = circumference * done / total if total else 0
    pct = round(100 * done / total) if total else 0
    legend = [("ok", f"{tones.count('ok')} done"), ("info", f"{tones.count('info')} in progress"),
              ("bad", f"{tones.count('bad')} blocked"), ("idle", f"{tones.count('idle')} not started")]
    legend_html = "".join(
        f'<div><i style="background:var(--{tone})"></i>{label}</div>'
        for tone, label in legend if not label.startswith("0 ")
    ) or '<div class="muted">No rows yet</div>'
    rows, next_marked = [], False
    for row in plan["rows"]:
        values = list(row.values())
        number, work, status = values[0], values[1], values[-1]
        tone, label = plan_tone(status)
        css = {"ok": "done", "bad": "blocked"}.get(tone, "")
        if tone != "ok" and not next_marked:
            next_marked = True
            if tone != "bad":
                css = "next"
        sub = [esc(column(row, "Covers"), empty="")] if filled(column(row, "Covers")) else []
        if tone == "bad":
            sub = [esc(status)]
        needs = column(row, "Needs")
        if tone != "ok" and filled(needs):
            sub.append("Needs: " + esc(needs))
        sub_html = f'<span>{" · ".join(sub)}</span>' if sub else ""
        rows.append(
            f'<li class="row {css}"><span class="row-num">{esc(number)}</span>'
            f'<span class="row-work"><strong>{esc(work)}</strong>{sub_html}</span>{chip(tone, label)}</li>'
        )
    ring = (
        f'<svg class="ring" viewBox="0 0 112 112" role="img" aria-label="{done} of {total} plan rows done">'
        f'<defs><linearGradient id="{uid}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{phase_color(plan["phase"])}"/>'
        f'<stop offset="1" stop-color="{phase_color(plan["phase"] + 1)}"/></linearGradient></defs>'
        f'<circle cx="56" cy="56" r="44" fill="none" stroke="var(--surface-2)" stroke-width="12"/>'
        + (f'<circle cx="56" cy="56" r="44" fill="none" stroke="url(#{uid})" stroke-width="12" stroke-linecap="round"'
           f' stroke-dasharray="{dash:.1f} {circumference:.1f}" transform="rotate(-90 56 56)"/>' if done else "")
        + f'<text x="56" y="58" text-anchor="middle" font-size="24" font-weight="600">{pct}%</text>'
        f'<text class="sub" x="56" y="76" text-anchor="middle" font-size="11">{done} of {total}</text></svg>'
    )
    return (
        f'<section class="card"><div class="card-head"><h2>{esc(plan["heading"])}</h2>'
        f'<span class="muted">One row per session</span></div>'
        f'<div class="plan-top">{ring}<div class="legend">{legend_html}</div></div>'
        f'<ol class="rows">{"".join(rows)}</ol></section>'
    )


def render_deliverables(text):
    rows = [r for r in section_rows(text, "Deliverables") if filled(column(r, "Deliverable"))]
    if not rows:
        return ""
    body = []
    for row in rows:
        phase = column(row, "Phase")
        match = re.match(r"\s*(\d+)", phase)
        color = phase_color(int(match.group(1))) if match else "var(--idle)"
        tone, label, note = deliverable_status(column(row, "Status"))
        status_html = chip(tone, label) if tone else esc("" if note else column(row, "Status"), empty="—")
        file_html = f'<span class="file mono">{esc(column(row, "File"), empty="")}</span>' \
            if filled(column(row, "File")) else ""
        note_html = f'<span class="note" title="{html.escape(note.replace("`", ""))}">{esc(note)}</span>' \
            if filled(note) else ""
        body.append(
            f'<tr><td><span class="ph" style="--c:{color}">{esc(phase)}</span></td>'
            f'<td>{esc(column(row, "Deliverable"))}{file_html}{note_html}</td>'
            f'<td class="mono tnum">{esc(column(row, "Version"))}</td><td>{status_html}</td></tr>'
        )
    return (
        f'<section class="card"><div class="card-head"><h2>Deliverables</h2>'
        f'<span class="muted">{len(rows)} tracked</span></div><div class="table-scroll"><table>'
        f'<thead><tr><th>Ph</th><th>Deliverable</th><th>Version</th><th>Status</th></tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div></section>'
    )


def render_gates(gate_list):
    if not gate_list:
        return ""
    tagged = [g["tag"] for g in gate_list if filled(g["tag"])]
    cards = []
    for g in gate_list:
        pending = g["tone"] == "pending"
        who = " · ".join(esc(v) for v in (g["date"], g["approver"]) if filled(v))
        cards.append(
            f'<div class="gate{" pending" if pending else ""}" style="--g:{phase_color(g["number"])}">'
            f'<div class="gate-id"><b>{esc(g["id"])}</b>{chip(g["tone"], g["label"])}</div>'
            f'<span class="gate-name">{esc(g["name"], empty="")}</span>'
            + (f'<span class="gate-who tnum">{who}</span>' if who else "")
            + (f'<span class="gate-cond">{esc(g["conditions"])}</span>' if filled(g["conditions"]) else "")
            + "</div>"
        )
    tag = f'<span class="muted mono">{esc(tagged[-1], empty="")}</span>' if tagged else ""
    return (
        f'<section class="card"><div class="card-head"><h2>Gates</h2>{tag}</div>'
        f'<div class="gates">{"".join(cards)}</div></section>'
    )


def risks(text):
    result = []
    for row in section_rows(text, "Risks"):
        description = column(row, "Risk")
        if not filled(description):
            continue
        likelihood = LEVEL.get(column(row, "Likelihood")[:1].lower())
        impact = LEVEL.get(column(row, "Impact")[:1].lower())
        result.append({
            "id": column(row, "ID"), "text": description, "owner": column(row, "Owner"),
            "likelihood": likelihood, "impact": impact,
            "score": (likelihood or 0) + (impact or 0), "open": is_open(column(row, "Status")),
        })
    return result


def heat_class(score):
    return "hi" if score >= 5 else "md" if score == 4 else "lo"


def render_risks(text, risk_list):
    items = [r for r in section_rows(text, "Open items") if filled(column(r, "Description"))]
    crs = [r for r in section_rows(text, "Change requests") if filled(column(r, "CR"))]
    if not (risk_list or items or crs):
        return ""
    open_risks = [r for r in risk_list if r["open"]]
    parts = []
    if risk_list:
        grid = []
        for likelihood, letter in ((3, "H"), (2, "M"), (1, "L")):
            grid.append(f'<span class="lbl">{letter}</span>')
            for impact in (1, 2, 3):
                n = sum(1 for r in open_risks if r["likelihood"] == likelihood and r["impact"] == impact)
                grid.append(f'<span class="cell {heat_class(likelihood + impact)}">{n or ""}</span>')
        grid.append('<span></span><span class="lbl">L</span><span class="lbl">M</span><span class="lbl">H</span>')
        grid.append('<span></span><span class="heat-axis">Impact → · ↑ Likelihood</span>')
        top = sorted(open_risks, key=lambda r: -r["score"])[:3]
        tone = {"hi": "bad", "md": "warn", "lo": "ok"}
        top_html = "".join(
            f'<li style="--r:var(--{tone[heat_class(r["score"])]})"><span class="rid">'
            + " · ".join(esc(v) for v in (r["id"], level_pair(r), r["owner"]) if filled(v))
            + f'</span><span>{esc(r["text"])}</span></li>'
            for r in top
        ) or '<li style="--r:var(--ok)">No open risks.</li>'
        parts.append(
            f'<div class="risk-wrap"><div class="heat" role="img" aria-label="{len(open_risks)} open risks '
            f'by likelihood and impact">{"".join(grid)}</div><ul class="risks">{top_html}</ul></div>'
        )
    mini = []
    if items:
        open_items = [r for r in items if is_open(column(r, "Status"))]
        blocking = sum(1 for r in open_items if blocks_gate(column(r, "Blocks")))
        mini.append(f'<div><span class="muted">Open items</span><b class="tnum">{len(open_items)}</b>'
                    f'<span>{blocking} block a gate</span></div>')
    if crs:
        pending = sum(1 for r in crs if not column(r, "Status").lower().startswith(
            ("approved", "rejected", "closed", "implemented", "done")))
        mini.append(f'<div><span class="muted">Change requests</span><b class="tnum">{len(crs)}</b>'
                    f'<span>{pending} awaiting a decision</span></div>')
    if mini:
        parts.append(f'<div class="mini">{"".join(mini)}</div>')
    closed = len(risk_list) - len(open_risks)
    return (
        f'<section class="card"><div class="card-head"><h2>Risks</h2>'
        f'<span class="muted">{len(open_risks)} open · {closed} closed</span></div>{"".join(parts)}</section>'
    )


def blocks_gate(cell):
    """True for "Yes", "Yes (G3)" or a gate ID such as "G3"; False for "No", "—" or empty."""
    return cell.strip().lower().startswith("y") or bool(re.match(r"\s*G\d", cell))


def handoff_value(text, name):
    """A "- **<name>:** value" Handoff line plus its indented continuation lines, as a list of parts."""
    lines = handoff_lines(text)
    pattern = re.compile(r"^[-*]\s*\*\*" + re.escape(name) + r":?\*\*:?\s*(.*)$", re.IGNORECASE)
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            parts = [match.group(1).strip()]
            for more in lines[i + 1:]:
                if not more[:1].isspace():
                    break
                parts.append(more.strip().lstrip("-*").strip())
            return [part for part in parts if part]
    return []


def rich(parts):
    """The first part as text, the rest as a short list under it."""
    if not parts:
        return ""
    more = "".join(f"<li>{esc(part)}</li>" for part in parts[1:])
    return esc(parts[0]) + (f'<ul class="more">{more}</ul>' if more else "")


def level_pair(risk):
    letters = {1: "L", 2: "M", 3: "H"}
    if risk["likelihood"] and risk["impact"]:
        return f'{letters[risk["likelihood"]]}/{letters[risk["impact"]]}'
    return ""


def render_handoff(text, current):
    lines = handoff_lines(text)
    if not lines:
        return ""
    values = {name: handoff_value(text, name) for name in
              ("Last session", "State", "Next action", "Load", "Inputs")}
    values = {name: parts for name, parts in values.items() if parts and filled(parts[0])}
    callouts = []
    if "Next action" in values:
        callouts.append(f'<div class="callout" style="--c:{phase_color(current or 1)}"><span class="k">Next action'
                        f'</span><p>{rich(values["Next action"])}</p></div>')
    waiting = handoff_field(text, "Waiting on user")
    if filled(waiting) and not waiting.lower().startswith(NOTHING):
        callouts.append(f'<div class="callout wait"><span class="k">Waiting on you</span>'
                        f'<p>{esc(waiting)}</p></div>')
    elif filled(waiting):
        callouts.append('<div class="callout clear"><span class="k">Waiting on you</span>'
                        '<p>Nothing. The next session can start.</p></div>')
    facts = [(name, values[name]) for name in ("Last session", "State", "Load", "Inputs") if name in values]
    if not callouts and not facts:  # a free-form handoff: show what's filled in, as written
        written = [line.lstrip("-* ").replace("**", "").strip() for line in lines]
        facts = [("", [line]) for line in written if filled(line) and not PLACEHOLDER.search(line)]
    if not callouts and not facts:
        return ""
    facts_html = "".join(f"<dt>{esc(name, empty='')}</dt><dd>{rich(parts)}</dd>" for name, parts in facts)
    return (
        f'<section class="card"><div class="card-head"><h2>Handoff</h2></div><div class="handoff">'
        f'{"".join(callouts)}' + (f'<dl class="facts">{facts_html}</dl>' if facts else "") + "</div></section>"
    )


def render_workspace(text, label, uid="w1", skill_dir=None, names=None):
    """One workspace's dashboard as an HTML <section>."""
    phases = phase_names(text, skill_dir, names)
    current = phase_number(text)
    plan = plan_progress(text)
    gate_list = gates(text)
    risk_list = risks(text)
    name = title_of(text, Path(label).name)
    tags = []
    if current and current in phases:
        tags.append(f'<span class="tag"><span class="dot" style="background:{phase_color(current)}"></span>'
                    f'Phase <b>{current} · {esc(phases[current])}</b></span>')
    for key in ("Type", "Code review mode", "Tailoring"):
        value = field(text, key)
        if filled(value) and " / " not in value:  # " / " marks an unchosen template option
            tags.append(f'<span class="tag">{esc(value)}</span>')
    updated = field(text, "Last updated")
    if filled(updated):
        tags.append(f'<span class="tag tnum">Updated {esc(updated)}</span>')
    hero = (
        f'<section class="hero" aria-label="Overview">'
        f'<div class="hero-glow" style="--c:{phase_color(current or 1)}" aria-hidden="true"></div>'
        f'<div class="hero-top"><div><div class="eyebrow">{esc(label)}</div><h1>{esc(name)}</h1></div>'
        f'<div class="hero-meta">{"".join(tags)}</div></div>'
        f'{render_stepper(phases, current, gate_list, plan)}</section>'
    )
    left = render_plan(plan, f"ring-{uid}") + render_deliverables(text)
    right = render_gates(gate_list) + render_risks(text, risk_list)
    board = f'<div class="board"><div class="col">{left}</div><div class="col">{right}</div></div>' \
        if left and right else f'<div class="col">{left or right}</div>'
    return (
        f'<section class="ws" aria-label="{esc(name)}">{hero}'
        f'{render_kpis(phases, current, plan, gate_list, risk_list)}'
        f'{board}{render_handoff(text, current)}</section>'
    )


def render_page(blocks, title, generated=None):
    generated = generated or datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f"<title>{html.escape(title)}</title>\n"
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600'
        '&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">\n'
        f"<style>{CSS}</style>\n</head>\n<body>\n<div class=\"wrap\">\n"
        + "\n".join(blocks)
        + f'\n<footer>Generated {html.escape(generated)} from STATUS.md by progress.py</footer>\n'
        "</div>\n</body>\n</html>\n"
    )


def find_project(start):
    """The nearest folder at or above `start` that has docs/sdlc/*/STATUS.md, or `start` itself."""
    start = Path(start).resolve()
    for folder in (start, *start.parents):
        if workspaces(folder):
            return folder
    return start


def select(project, workspace=None):
    """The workspace folders to show: the one named by a slug ("notes-app"), a path ("docs/sdlc/notes-app")
    or a STATUS.md path, or every workspace when none is named. Raises SystemExit when there's none."""
    project = Path(project).resolve()
    found = workspaces(project)
    if not workspace:
        if not found:
            raise SystemExit(f"No docs/sdlc/*/STATUS.md in {project}. Run this from your project, or pass --project.")
        return found
    for candidate in (Path(workspace), project / workspace, project / "docs/sdlc" / workspace):
        candidate = candidate.resolve()
        if candidate.name == "STATUS.md":
            candidate = candidate.parent
        if (candidate / "STATUS.md").is_file():
            return [candidate]
    names = ", ".join(path.name for path in found) or "none"
    raise SystemExit(f"No workspace {workspace!r}. Workspaces in {project}: {names}.")


def label_of(project, path):
    try:
        return str(path.relative_to(project))
    except ValueError:
        return path.name


def build(project, workspace=None, skill_dir=None, names=None, out=None):
    """Writes the dashboard and returns its path. Raises SystemExit with a message when there's nothing to show."""
    project = Path(project).resolve()
    found = select(project, workspace)
    texts = [(path / "STATUS.md").read_text(encoding="utf-8") for path in found]
    blocks = [render_workspace(text, label_of(project, path), f"w{i}", skill_dir, names)
              for i, (path, text) in enumerate(zip(found, texts), 1)]
    title = title_of(texts[0], found[0].name) + " progress" if len(found) == 1 else "SDLC progress"
    target = Path(out) if out else (found[0] if len(found) == 1 else found[0].parent) / "progress.html"
    target.write_text(render_page(blocks, title), encoding="utf-8")
    return target


def summary(text, label, skill_dir=None, names=None):
    """A few plain-text lines on where a workspace stands, for the terminal."""
    phases = phase_names(text, skill_dir, names)
    current = phase_number(text)
    head = title_of(text, Path(label).name)
    if current:
        head += f" · Phase {current}" + (f" {phases[current]}" if current in phases else "")
    lines = [head]
    plan = plan_progress(text)
    if plan:
        line = f'  Plan     {plan["done"]}/{plan["total"]} done'
        open_rows = [row for row in plan["rows"] if plan_tone(list(row.values())[-1])[0] != "ok"]
        if open_rows:
            values = list(open_rows[0].values())
            line += f" · next: #{values[0]} {values[1]} ({values[-1]})"
        lines.append(line)
    gate_list = gates(text)
    decided = [f'{g["id"]} {g["label"].lower()}' for g in gate_list if g["tone"] != "pending"]
    upcoming = [f'{g["id"]} next' for g in gate_list if g["label"] == "Next"]
    if gate_list:
        lines.append("  Gates    " + " · ".join(decided + upcoming))
    waiting = handoff_field(text, "Waiting on user")
    if filled(waiting):
        lines.append(f"  Waiting on you: {waiting}")
    return "\n".join(lines)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Render SDLC STATUS.md files as a progress dashboard (progress.html) and print a summary.")
    parser.add_argument("workspace", nargs="?",
                        help='a workspace slug ("notes-app") or path (default: every workspace)')
    parser.add_argument("--workspace", dest="workspace_option", help=argparse.SUPPRESS)
    parser.add_argument("--project", help="the project root (default: found from the current folder upwards)")
    parser.add_argument("--skill-dir", help="a skill folder whose phases/<n>-<name>.md files name the phases")
    parser.add_argument("--phases", help='comma-separated phase names, e.g. "Discovery,Build,Launch"')
    parser.add_argument("--out", help="where to write the page (default: progress.html next to STATUS.md)")
    parser.add_argument("--open", action="store_true", help="open the page in the default browser")
    parser.add_argument("--quiet", action="store_true", help="print only the page's path")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    workspace = args.workspace or args.workspace_option
    project = Path(args.project).resolve() if args.project else find_project(Path.cwd())
    names = args.phases.split(",") if args.phases else None
    target = build(project, workspace, args.skill_dir, names, args.out)
    if not args.quiet:
        for path in select(project, workspace):
            print(summary((path / "STATUS.md").read_text(encoding="utf-8"), label_of(project, path),
                          args.skill_dir, names))
            print()
        print("Dashboard: ", end="")
    print(target.resolve())
    if args.open:
        webbrowser.open(target.resolve().as_uri())
    return 0


CSS = """
/* Layout: a phase-colored hero with a stepper, a KPI strip, a two-column board, the handoff last. */
:root {
  --bg: #f6f7fb; --surface: #ffffff; --surface-2: #eef0f7; --fg: #171a2b; --muted: #5d6480; --line: #dfe2ee;
  --shadow: 0 1px 2px rgba(23,26,43,.05), 0 8px 24px rgba(23,26,43,.06);
  --p1: #7c3aed; --p2: #2563eb; --p3: #0891b2; --p4: #16a34a; --p5: #d97706; --p6: #ea580c; --p7: #db2777;
  --ok: #15803d; --ok-bg: #dcfce7; --warn: #b45309; --warn-bg: #fef3c7; --bad: #b91c1c; --bad-bg: #fee2e2;
  --info: #1d4ed8; --info-bg: #dbeafe; --idle: #64748b; --idle-bg: #eef1f6;
  --font-display: "Space Grotesk", "Segoe UI", system-ui, sans-serif;
  --font-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace;
  --radius: 16px;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #0e1020; --surface: #171a2e; --surface-2: #20243b; --fg: #eceefa; --muted: #a0a6c4; --line: #2b3050;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 10px 30px rgba(0,0,0,.25);
    --p1: #a78bfa; --p2: #60a5fa; --p3: #22d3ee; --p4: #4ade80; --p5: #fbbf24; --p6: #fb923c; --p7: #f472b6;
    --ok: #4ade80; --ok-bg: rgba(74,222,128,.14); --warn: #fbbf24; --warn-bg: rgba(251,191,36,.14);
    --bad: #f87171; --bad-bg: rgba(248,113,113,.15); --info: #60a5fa; --info-bg: rgba(96,165,250,.15);
    --idle: #94a3b8; --idle-bg: rgba(148,163,184,.12);
    color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #0e1020; --surface: #171a2e; --surface-2: #20243b; --fg: #eceefa; --muted: #a0a6c4; --line: #2b3050;
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 10px 30px rgba(0,0,0,.25);
  --p1: #a78bfa; --p2: #60a5fa; --p3: #22d3ee; --p4: #4ade80; --p5: #fbbf24; --p6: #fb923c; --p7: #f472b6;
  --ok: #4ade80; --ok-bg: rgba(74,222,128,.14); --warn: #fbbf24; --warn-bg: rgba(251,191,36,.14);
  --bad: #f87171; --bad-bg: rgba(248,113,113,.15); --info: #60a5fa; --info-bg: rgba(96,165,250,.15);
  --idle: #94a3b8; --idle-bg: rgba(148,163,184,.12);
  color-scheme: dark;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--fg); font: 400 15px/1.55 var(--font-body);
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  padding-block: 24px 48px;
}
.wrap { max-width: 1120px; margin: 0 auto; display: grid; gap: 40px; }
.ws { display: grid; gap: 20px; min-width: 0; }
h1, h2 { font-family: var(--font-display); margin: 0; text-wrap: balance; }
.mono { font-family: var(--font-mono); font-size: .86em; }
.muted { color: var(--muted); }
.tnum { font-variant-numeric: tabular-nums; }

.hero { position: relative; overflow: hidden; background: var(--surface); border-radius: 22px; box-shadow: var(--shadow);
  padding: 26px 26px 22px; display: grid; gap: 22px; }
.spectrum { position: absolute; inset: 0 0 auto 0; height: 6px; display: grid; }
.spectrum span.later { opacity: .25; }
.hero-glow { position: absolute; width: 420px; height: 420px; right: -140px; top: -220px; border-radius: 50%;
  background: radial-gradient(closest-side, color-mix(in srgb, var(--c) 28%, transparent), transparent); pointer-events: none; }
.hero-top { display: flex; flex-wrap: wrap; gap: 14px 24px; align-items: flex-end; justify-content: space-between; position: relative; }
.hero-top > div:first-child { min-width: 0; }
.eyebrow { font-size: 12px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 600; overflow-wrap: anywhere; }
.hero h1 { font-size: clamp(26px, 4vw, 36px); letter-spacing: -.02em; line-height: 1.1; margin-top: 4px; }
.hero-meta { display: flex; flex-wrap: wrap; gap: 8px; }
.tag { display: inline-flex; align-items: center; gap: 6px; padding: 5px 11px; border-radius: 999px;
  background: var(--surface-2); font-size: 13px; color: var(--fg); }
.tag b { font-weight: 600; }
.tag .dot { width: 8px; height: 8px; border-radius: 50%; }

.stepper-scroll { overflow-x: auto; position: relative; margin: 0 -6px; padding: 6px; }
.stepper { display: grid; list-style: none; margin: 0; padding: 0; }
.step { position: relative; display: grid; justify-items: center; align-content: start; gap: 8px; text-align: center; }
.step::before { content: ""; position: absolute; top: 17px; right: 50%; width: 100%; height: 4px; border-radius: 4px; background: var(--line); }
.step:first-child::before { display: none; }
.step.done::before, .step.now::before { background: linear-gradient(90deg, var(--prev), var(--c)); }
.node { position: relative; z-index: 1; width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center;
  font: 600 14px var(--font-display); background: var(--surface); color: var(--muted); border: 2px solid var(--line); }
.step.done .node { background: var(--c); border-color: var(--c); color: #fff; }
.step.now .node { border: 3px solid var(--c); color: var(--c); animation: pulse 2.4s ease-in-out infinite;
  box-shadow: 0 0 0 6px color-mix(in srgb, var(--c) 18%, transparent); }
@keyframes pulse {
  0%,100% { box-shadow: 0 0 0 5px color-mix(in srgb, var(--c) 20%, transparent); }
  50% { box-shadow: 0 0 0 11px color-mix(in srgb, var(--c) 6%, transparent); }
}
@media (prefers-reduced-motion: reduce) { .step.now .node { animation: none; } }
.step-name { font-size: 13px; font-weight: 600; line-height: 1.25; }
.step.later .step-name { color: var(--muted); font-weight: 500; }
.step-sub { font-size: 11.5px; color: var(--muted); margin-top: -4px; }
.step.now .step-sub { color: var(--c); font-weight: 600; }

.kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; }
.kpi { background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); padding: 16px 18px; display: grid; gap: 4px; min-width: 0; }
.kpi-label { font-size: 12px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
.kpi-value { font: 600 26px/1.1 var(--font-display); font-variant-numeric: tabular-nums; }
.kpi-value small { font-size: 15px; color: var(--muted); font-weight: 500; }
.kpi-bar { height: 6px; border-radius: 6px; background: var(--surface-2); overflow: hidden; margin-top: 6px; }
.kpi-bar i { display: block; height: 100%; border-radius: 6px; }

.board { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); gap: 20px; align-items: start; }
.col { display: grid; gap: 20px; min-width: 0; }
.card { background: var(--surface); border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px; display: grid; gap: 16px; min-width: 0; }
.card-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.card-head h2 { font-size: 18px; letter-spacing: -.01em; }
.card-head .muted { font-size: 13px; }

.plan-top { display: flex; gap: 20px; align-items: center; flex-wrap: wrap; }
.ring { width: 112px; height: 112px; flex: none; }
.ring text { fill: var(--fg); font-family: var(--font-display); }
.ring .sub { fill: var(--muted); font-family: var(--font-body); }
.legend { display: grid; gap: 6px; font-size: 13.5px; }
.legend div { display: flex; align-items: center; gap: 8px; }
.legend i { width: 10px; height: 10px; border-radius: 3px; display: inline-block; }
.rows { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.row { display: grid; grid-template-columns: 30px minmax(0, 1fr) auto; gap: 12px; align-items: center; padding: 10px 12px;
  border-radius: 12px; background: var(--surface-2); }
.row.next { background: color-mix(in srgb, var(--info) 10%, var(--surface)); outline: 1.5px solid color-mix(in srgb, var(--info) 45%, transparent); }
.row-num { width: 28px; height: 28px; border-radius: 8px; display: grid; place-items: center; font: 600 13px var(--font-display);
  background: var(--surface); color: var(--muted); }
.row.done .row-num { background: var(--ok-bg); color: var(--ok); }
.row.next .row-num { background: var(--info); color: #fff; }
.row.blocked .row-num { background: var(--bad-bg); color: var(--bad); }
.row-work { min-width: 0; overflow-wrap: anywhere; }
.row-work strong { font-weight: 600; font-size: 14.5px; display: block; }
.row-work span { font-size: 12.5px; color: var(--muted); }
.row.done .row-work strong { color: var(--muted); text-decoration: line-through; text-decoration-color: color-mix(in srgb, var(--muted) 50%, transparent); }

.chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12.5px;
  font-weight: 600; white-space: nowrap; max-width: 220px; overflow: hidden; text-overflow: ellipsis; }
.chip::before { content: ""; width: 7px; height: 7px; border-radius: 50%; background: currentColor; flex: none; }
.chip.ok { background: var(--ok-bg); color: var(--ok); }
.chip.warn { background: var(--warn-bg); color: var(--warn); }
.chip.bad { background: var(--bad-bg); color: var(--bad); }
.chip.info { background: var(--info-bg); color: var(--info); }
.chip.idle { background: var(--idle-bg); color: var(--idle); }
.chip.pending { background: transparent; color: var(--muted); border: 1.5px dashed var(--line); }
.chip.pending::before { background: var(--line); }

.gates { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.gate { border-radius: 12px; padding: 12px; display: grid; gap: 6px; align-content: start; min-width: 0;
  background: var(--surface-2); border-top: 4px solid var(--g); overflow-wrap: anywhere; }
.gate.pending { background: transparent; border: 1.5px dashed var(--line); border-top: 4px solid color-mix(in srgb, var(--g) 35%, var(--line)); }
.gate-id { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.gate-id b { font: 600 15px var(--font-display); }
.gate-name { font-size: 13px; font-weight: 500; }
.gate-who { font-size: 12px; color: var(--muted); }
.gate-cond { font-size: 12px; color: var(--warn); }

.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font-size: 11.5px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); font-weight: 600; padding: 0 10px 8px; }
td { padding: 10px; border-top: 1px solid var(--line); vertical-align: middle; }
td:first-child, th:first-child { padding-left: 0; }
td:last-child, th:last-child { padding-right: 0; text-align: right; }
.ph { display: inline-grid; place-items: center; min-width: 24px; height: 24px; padding: 0 5px; border-radius: 7px; color: #fff;
  font: 600 12px var(--font-display); background: var(--c); white-space: nowrap; }
.file { display: block; font-size: 12px; color: var(--muted); }
.note { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  max-width: 52ch; margin-top: 2px; font-size: 12px; color: var(--muted); }

.risk-wrap { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 18px; align-items: start; }
.heat { display: grid; grid-template-columns: 22px repeat(3, 34px); grid-auto-rows: 34px; gap: 4px; font-size: 11px; color: var(--muted); }
.heat .lbl { display: grid; place-items: center; font-weight: 600; }
.cell { border-radius: 8px; display: grid; place-items: center; font: 600 13px var(--font-display); color: var(--fg); }
.lo { background: color-mix(in srgb, var(--ok) 22%, var(--surface)); }
.md { background: color-mix(in srgb, var(--warn) 32%, var(--surface)); }
.hi { background: color-mix(in srgb, var(--bad) 40%, var(--surface)); }
.heat-axis { grid-column: 2 / -1; text-align: center; font-size: 11px; }
.risks { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; font-size: 13.5px; min-width: 0; }
.risks li { display: grid; gap: 2px; padding-left: 12px; border-left: 3px solid var(--r); overflow-wrap: anywhere; }
.risks .rid { font-family: var(--font-mono); font-size: 12px; color: var(--muted); }
.mini { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.mini > div { background: var(--surface-2); border-radius: 12px; padding: 12px; display: grid; gap: 4px; font-size: 13px; }
.mini b { font: 600 20px var(--font-display); }

.handoff { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; align-items: start; }
.more { margin: 6px 0 0; padding-left: 18px; display: grid; gap: 2px; font-size: .92em; font-weight: 400; color: var(--muted); }
.callout { border-radius: 14px; padding: 16px 18px; display: grid; gap: 6px; align-content: start; overflow-wrap: anywhere;
  background: color-mix(in srgb, var(--c) 10%, var(--surface)); border: 1px solid color-mix(in srgb, var(--c) 35%, transparent); }
.callout.wait { --c: var(--warn); background: var(--warn-bg); }
.callout.clear { --c: var(--ok); }
.callout .k { font-size: 12px; letter-spacing: .06em; text-transform: uppercase; font-weight: 700; color: var(--c); }
.callout p { margin: 0; font-size: 15px; font-weight: 500; }
.facts { grid-column: 1 / -1; display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 6px 16px; font-size: 13.5px; margin: 0; }
.facts dt { color: var(--muted); font-weight: 500; }
.facts dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }

footer { font-size: 12.5px; color: var(--muted); text-align: center; }

@media (max-width: 900px) { .board { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 560px) {
  .hero { padding: 22px 18px 18px; }
  .gates, .risk-wrap { grid-template-columns: minmax(0, 1fr); }
  .card { padding: 16px; }
}
"""

if __name__ == "__main__":
    sys.exit(main())
