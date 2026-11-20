"""Tests for the progress dashboard. Run from the repo root: python3 -m unittest discover -s scripts/test"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / "hooks"))
import progress  # noqa: E402

FILLED = """# STATUS: Notes App

| Field | Value |
|---|---|
| Type | New app |
| Code review mode | Review after writing |
| Current phase | 3 Detailed design |
| Last updated | 2026-11-18 |

## Deliverables
| Phase | Deliverable | File | Status (Not started / Draft / In review / Approved) | Version |
|---|---|---|---|---|
| 1 | Requirements | requirements.md | Approved | v1.0 |
| 3 | Feature designs | design/<feature>.md | In review | v0.6 |
| 6 | Release checklist | release-checklist.md | Not started | — |

## Gate log
| Gate | Date | Decision | Approver (name, role) | Conditions or accepted risk | Tag |
|---|---|---|---|---|---|
| G1 Requirements baseline | 2026-10-21 | Approved | A. Tran, PO | | sdlc/notes/G1 |
| G2 Architecture baseline | 2026-11-06 | Approved with conditions | B. Le, TL | Pen test before G5 | sdlc/notes/G2 |
| G3 Ready to build | | | | | |

## Risks
| ID | Risk ("If …, then …") | Likelihood (H/M/L) | Impact (H/M/L) | Owner | Mitigation | Status |
|---|---|---|---|---|---|---|
| R-01 | If the API slips, then G3 moves | H | H | TL | Mock server | Open |
| R-02 | If designs drift, then rework | L | M | Designer | — | Closed |

## Open items
| ID | Type (TBD / ASSUMPTION / Question) | Description | Blocks gate? | Owner | Status |
|---|---|---|---|---|---|
| TBD-3 | TBD | Privacy copy | Yes (G3) | PO | Open |

## Phase 3 plan
| # | Work | Covers | Needs from the owner | Status |
|---|---|---|---|---|
| 1 | Design login | FR-001 | — | Done 2026-11-08 |
| 2 | Design notes list | FR-005 | — | Done |
| 3 | Design sync <script>alert(1)</script> | FR-011 | — | In progress |
| 4 | Design settings | FR-020 | Privacy copy | Blocked: privacy copy |

## Handoff
<!-- guidance -->
- **Last session:** 2026-11-18 — finished the notes list
- **Next action:** write the conflict states in `design/sync.md`
- **Waiting on user:** Privacy copy (TBD-3)
"""


def render(text, **kwargs):
    return progress.render_page([progress.render_workspace(text, "docs/sdlc/notes", **kwargs)], "t", "now")


class RenderTest(unittest.TestCase):
    def test_phases_come_from_the_owning_skill(self):
        page = render(FILLED)
        for name in ("Requirements", "Architecture", "Detailed design", "Implementation", "Maintenance"):
            self.assertIn(f'<span class="step-name">{name}</span>', page)
        self.assertEqual(page.count('class="step done"'), 2)
        self.assertEqual(page.count('class="step now"'), 1)
        self.assertEqual(page.count('class="step later"'), 4)
        self.assertIn("In progress · 2/4", page)

    def test_plan_progress_and_row_states(self):
        page = render(FILLED)
        self.assertIn("2<small> / 4 done</small>", page)
        self.assertIn('aria-label="2 of 4 plan rows done"', page)
        self.assertIn('<li class="row next">', page)
        self.assertIn('<li class="row blocked">', page)
        self.assertIn("Blocked: privacy copy", page)

    def test_gates_deliverables_and_risks(self):
        page = render(FILLED)
        self.assertIn('<span class="chip ok">Approved</span>', page)
        self.assertIn('<span class="chip warn">With conditions</span>', page)
        self.assertIn('<span class="chip pending">Next</span>', page)
        self.assertIn("2<small> / 3</small>", page)  # gates passed
        self.assertIn('<span class="chip info">In review</span>', page)
        self.assertIn("1 open · 1 closed", page)
        self.assertIn("1 block a gate", page)

    def test_handoff_highlights_what_waits_on_the_user(self):
        page = render(FILLED)
        self.assertIn('<div class="callout wait">', page)
        self.assertIn('<span class="mono">design/sync.md</span>', page)
        self.assertNotIn("guidance", page)
        cleared = render(FILLED.replace("Privacy copy (TBD-3)", "nothing"))
        self.assertIn('<div class="callout clear">', cleared)

    def test_escapes_status_text(self):
        page = render(FILLED)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_custom_phase_names(self):
        page = render(FILLED.replace("3 Detailed design", "2 Build"), names=["Discovery", "Build", "Launch"])
        self.assertIn('<span class="step-name">Launch</span>', page)
        self.assertNotIn("Maintenance", page)
        self.assertEqual(page.count('class="step now"'), 1)

    def test_phases_from_another_skills_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            phases = Path(tmp, "phases")
            phases.mkdir()
            for name in ("1-discovery.md", "2-user-research.md", "3-launch.md"):
                (phases / name).write_text("x", encoding="utf-8")
            page = render(FILLED.replace("3 Detailed design", "2 User research"), skill_dir=tmp)
        self.assertIn('<span class="step-name">User research</span>', page)
        self.assertNotIn("Detailed design", page)

    def test_missing_sections_are_left_out(self):
        minimal = "# STATUS: Tiny\n\n| Field | Value |\n|---|---|\n| Current phase | 1 Start |\n"
        page = render(minimal, names=["Start", "Finish"])
        for absent in ("<h2>Gates</h2>", "<h2>Deliverables</h2>", "<h2>Risks</h2>", "<h2>Handoff</h2>", "plan</h2>"):
            self.assertNotIn(absent, page)
        self.assertIn("<h1>Tiny</h1>", page)

    def test_status_from_before_the_rename_still_gets_phase_names(self):
        old = "# STATUS: Old\n\n| Field | Value |\n|---|---|\n| Skill | react-webapp-sdlc |\n| Current phase | 3 Detailed design |\n"
        self.assertEqual(progress.phase_names(old)[3], "Detailed design")

    def test_the_blank_template_renders_without_placeholders(self):
        for skill in ("react-webapp",):
            with self.subTest(skill=skill):
                text = (REPO / "skills" / skill / "templates/status.md").read_text(encoding="utf-8")
                page = render(text)
                self.assertNotIn("<h2>Handoff</h2>", page)  # only placeholders there
                self.assertNotIn("&lt;e.g.", page)
                self.assertIn("0 of 0", page)
                self.assertEqual(page.count('class="step now"'), 1)


class RealWorldCellsTest(unittest.TestCase):
    """Cells as long-running projects write them: notes in the status, gate IDs, multi-line handoffs."""

    def test_deliverable_status_splits_the_stage_from_its_note(self):
        self.assertEqual(progress.deliverable_status("Approved (G1, 2026-11-18)"), ("ok", "Approved", "G1, 2026-11-18"))
        self.assertEqual(progress.deliverable_status("Draft"), ("warn", "Draft", ""))
        self.assertEqual(progress.deliverable_status("ADR-0001 layout, ADR-0002 i18n: Proposed")[:2],
                         ("info", "Proposed"))
        mixed = "§1, §5 Approved (G1); master plan §2–§4 Draft"
        self.assertEqual(progress.deliverable_status(mixed), ("warn", "Draft", mixed))
        self.assertEqual(progress.deliverable_status("see ADR index"), (None, "", "see ADR index"))

    def test_a_gate_id_counts_as_blocking(self):
        self.assertTrue(progress.blocks_gate("G3"))
        self.assertTrue(progress.blocks_gate("Yes (G2)"))
        self.assertFalse(progress.blocks_gate("No"))
        self.assertFalse(progress.blocks_gate("—"))

    def test_handoff_fields_keep_their_continuation_lines(self):
        text = FILLED.replace("- **Last session:** 2026-11-18 — finished the notes list",
                              "- **Last session:** 2026-11-18 — row 2 done.\n  - list screen\n  - empty state")
        self.assertEqual(progress.handoff_value(text, "Last session"),
                         ["2026-11-18 — row 2 done.", "list screen", "empty state"])
        page = render(text)
        self.assertIn('<ul class="more"><li>list screen</li><li>empty state</li></ul>', page)

    def test_code_in_a_risk_stays_inline(self):
        page = render(FILLED.replace("If the API slips", "If `ALLOWED_ORIGINS` slips"))
        self.assertIn('<span>If <span class="mono">ALLOWED_ORIGINS</span> slips, then G3 moves</span>', page)


class CommandTest(unittest.TestCase):
    def test_writes_progress_html_next_to_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            for slug in ("notes", "sync"):
                workspace = Path(tmp, "docs/sdlc", slug)
                workspace.mkdir(parents=True)
                (workspace / "STATUS.md").write_text(FILLED, encoding="utf-8")
            one = subprocess.run([sys.executable, str(SCRIPTS / "progress.py"), "--workspace", "docs/sdlc/notes"],
                                 cwd=tmp, capture_output=True, text=True)
            self.assertEqual(one.returncode, 0, one.stderr)
            self.assertTrue(Path(tmp, "docs/sdlc/notes/progress.html").is_file())
            both = subprocess.run([sys.executable, str(SCRIPTS / "progress.py")], cwd=tmp, capture_output=True,
                                  text=True)
            page = Path(tmp, "docs/sdlc/progress.html").read_text(encoding="utf-8")
            self.assertEqual(both.returncode, 0, both.stderr)
            self.assertEqual(page.count('<section class="ws"'), 2)

    def test_takes_a_slug_from_anywhere_in_the_project_and_prints_a_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp, "docs/sdlc/notes")
            workspace.mkdir(parents=True)
            (workspace / "STATUS.md").write_text(FILLED, encoding="utf-8")
            done = subprocess.run([sys.executable, str(SCRIPTS / "progress.py"), "notes"], cwd=workspace,
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertTrue((workspace / "progress.html").is_file())
        self.assertIn("Notes App · Phase 3 Detailed design", done.stdout)
        self.assertIn("2/4 done · next: #3", done.stdout)
        self.assertIn("G1 approved · G2 with conditions · G3 next", done.stdout)
        self.assertIn("Waiting on you: Privacy copy (TBD-3)", done.stdout)
        self.assertIn("Dashboard: ", done.stdout)

    def test_names_the_workspaces_when_the_slug_is_wrong(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "docs/sdlc/notes").mkdir(parents=True)
            Path(tmp, "docs/sdlc/notes/STATUS.md").write_text(FILLED, encoding="utf-8")
            done = subprocess.run([sys.executable, str(SCRIPTS / "progress.py"), "nope"], cwd=tmp,
                                  capture_output=True, text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("No workspace 'nope'", done.stderr)
        self.assertIn(": notes.", done.stderr)

    def test_says_when_there_is_no_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            done = subprocess.run([sys.executable, str(SCRIPTS / "progress.py")], cwd=tmp, capture_output=True,
                                  text=True)
        self.assertEqual(done.returncode, 1)
        self.assertIn("No docs/sdlc/*/STATUS.md", done.stderr)


if __name__ == "__main__":
    unittest.main()
