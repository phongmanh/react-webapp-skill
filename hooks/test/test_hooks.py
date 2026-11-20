"""Tests for the SDLC hooks. Run from the repo root: python3 -m unittest discover -s hooks/test"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS))
from sdlc_status import column, plan_progress, section_rows, table_rows  # noqa: E402

STATUS = """# STATUS: Demo

| Field | Value |
|---|---|
| Current phase | 4 Implementation: in progress |
| Last updated | 2026-11-10 |

## Deliverables
| Phase | Deliverable | File | Status (Not started / Draft / In review / Approved) | Version |
|---|---|---|---|---|
| 1 | Requirements | requirements.md | Approved | 1.0 |

## Phase 3 plan
| # | Work | Covers | Needs from the owner | Status |
|---|---|---|---|---|
| 1 | Old design | FR-001 | — | Not started |

## Phase 4 plan
| # | PR | Covers | Needs from the owner | Status |
|---|---|---|---|---|
| 1 | Skeleton | ADR-0002 | — | Done 2026-10-23 |
| 2 | Domain | NFR-COMPAT-02 | — | Not started |
"""

HANDOFF = """
## Handoff
<!-- guidance -->
- **Next action:** plan PR 2
- **Load:** design/app-shell.md §5
"""


def run_hook(name, project, payload, **env):
    return subprocess.run(
        [sys.executable, str(HOOKS / name)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(project), "SDLC_GATE": "", **env},
        check=True,
    )


class ProjectTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.workspace = self.project / "docs/sdlc/demo"
        self.workspace.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_status(self, text):
        (self.workspace / "STATUS.md").write_text(text, encoding="utf-8")


class SessionContextTest(ProjectTestCase):
    def test_reports_phase_and_next_item_of_the_newest_plan(self):
        self.write_status(STATUS)
        out = run_hook("session-context.py", self.project, {"source": "clear"}).stdout
        self.assertIn("docs/sdlc/demo/", out)
        self.assertIn("Current phase: 4 Implementation: in progress", out)
        self.assertIn("Next plan item: Phase 4 plan #2: Domain (Not started)", out)
        self.assertNotIn("Handoff", out)

    def test_injects_the_handoff_without_comments(self):
        self.write_status(STATUS + HANDOFF)
        out = run_hook("session-context.py", self.project, {"source": "clear"}).stdout
        self.assertIn("Handoff from the last session", out)
        self.assertIn("- **Next action:** plan PR 2", out)
        self.assertNotIn("guidance", out)

    def test_caps_a_long_handoff(self):
        long = "\n## Handoff\n" + "\n".join(f"- line {i}" for i in range(50)) + "\n"
        self.write_status(STATUS + long)
        out = run_hook("session-context.py", self.project, {}).stdout
        self.assertIn("- line 29", out)
        self.assertNotIn("- line 30", out)
        self.assertIn("truncated", out)

    def test_says_when_the_gate_is_off(self):
        self.write_status(STATUS)
        out = run_hook("session-context.py", self.project, {}, SDLC_GATE="off").stdout
        self.assertIn("SDLC_GATE=off", out)

    def test_prints_nothing_without_a_workspace(self):
        (self.workspace / "STATUS.md").unlink(missing_ok=True)
        self.assertEqual(run_hook("session-context.py", self.project, {}).stdout, "")


class BaselineGuardTest(ProjectTestCase):
    def edit(self, relative_path, **env):
        payload = {"tool_name": "Edit", "tool_input": {"file_path": str(self.workspace / relative_path)}}
        return run_hook("guard-sdlc-baseline.py", self.project, payload, **env).stdout

    def test_asks_before_editing_a_baselined_document(self):
        self.write_status(STATUS)
        decision = json.loads(self.edit("requirements.md"))["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "ask")
        self.assertIn("SDLC_GATE=off", decision["permissionDecisionReason"])

    def test_lets_living_files_through(self):
        self.write_status(STATUS)
        self.assertEqual(self.edit("STATUS.md"), "")

    def test_gate_off_lets_baselined_documents_through(self):
        self.write_status(STATUS)
        self.assertEqual(self.edit("requirements.md", SDLC_GATE="OFF"), "")


class LargeReadGuardTest(ProjectTestCase):
    def read(self, path, **tool_input):
        payload = {"tool_name": "Read", "tool_input": {"file_path": str(path), **tool_input}}
        return run_hook("guard-large-read.py", self.project, payload).stdout

    def large_design(self):
        body = "".join(f"## {n}. Section\n" + "x" * 2000 + "\n" for n in range(1, 21))
        path = self.workspace / "design/menu.md"
        path.parent.mkdir()
        path.write_text("# Feature design: Menu\n" + body, encoding="utf-8")
        return path

    def test_refuses_a_whole_read_of_a_large_document_and_returns_its_outline(self):
        decision = json.loads(self.read(self.large_design()))["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("1: # Feature design: Menu", decision["permissionDecisionReason"])
        self.assertIn("2: ## 1. Section", decision["permissionDecisionReason"])

    def test_lets_a_narrow_ranged_read_through(self):
        self.assertEqual(self.read(self.large_design(), offset=2, limit=4), "")

    def test_refuses_a_range_that_covers_most_of_a_large_document(self):
        decision = json.loads(self.read(self.large_design(), offset=2, limit=40))["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("That range", decision["permissionDecisionReason"])
        self.assertIn("2: ## 1. Section", decision["permissionDecisionReason"])

    def test_lets_small_files_and_files_outside_the_workspace_through(self):
        self.write_status(STATUS)
        self.assertEqual(self.read(self.workspace / "STATUS.md"), "")
        outside = self.project / "big.md"
        outside.write_text("x" * 30_000, encoding="utf-8")
        self.assertEqual(self.read(outside), "")


class RefreshProgressTest(ProjectTestCase):
    def edit_status(self):
        payload = {"tool_name": "Edit", "tool_input": {"file_path": str(self.workspace / "STATUS.md")}}
        return run_hook("refresh-progress.py", self.project, payload)

    def test_creates_no_dashboard_nobody_asked_for(self):
        self.write_status(STATUS)
        self.edit_status()
        self.assertFalse((self.workspace / "progress.html").exists())

    def test_refreshes_an_existing_dashboard(self):
        self.write_status(STATUS)
        page = self.workspace / "progress.html"
        page.write_text("old", encoding="utf-8")
        done = self.edit_status()
        self.assertEqual(done.stdout, "")
        self.assertIn("Phase 4 plan", page.read_text(encoding="utf-8"))

    def test_ignores_other_files_and_never_fails(self):
        self.write_status("not a status file")
        page = self.workspace / "progress.html"
        page.write_text("old", encoding="utf-8")
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(self.workspace / "requirements.md")}}
        run_hook("refresh-progress.py", self.project, payload)
        self.assertEqual(page.read_text(encoding="utf-8"), "old")
        self.edit_status()  # a STATUS.md without the usual sections still renders, and the hook exits 0


class StatusTablesTest(unittest.TestCase):
    def test_section_rows_key_cells_by_header(self):
        rows = section_rows(STATUS, "deliverables")
        self.assertEqual(len(rows), 1)
        self.assertEqual(column(rows[0], "Status"), "Approved")
        self.assertEqual(column(rows[0], "version"), "1.0")
        self.assertEqual(column(rows[0], "Missing"), "")
        self.assertEqual(section_rows(STATUS, "Risks"), [])

    def test_table_rows_read_only_the_first_table(self):
        body = "| A | B |\n|---|---|\n| 1 | 2 |\n\ntext\n\n| C |\n|---|\n| 3 |\n"
        self.assertEqual(table_rows(body), [{"A": "1", "B": "2"}])

    def test_plan_progress_reads_the_newest_plan(self):
        plan = plan_progress(STATUS)
        self.assertEqual((plan["heading"], plan["phase"], plan["done"], plan["total"]), ("Phase 4 plan", 4, 1, 2))
        self.assertIsNone(plan_progress("# nothing"))


if __name__ == "__main__":
    unittest.main()
