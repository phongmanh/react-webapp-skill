"""Tests for the autopilot driver. Run from the repo root: python3 -m unittest discover -s scripts/test"""
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS.parent / "hooks"))
from sdlc_status import handoff_field, next_plan_row  # noqa: E402

PLAN_ROWS = """| 1 | Draft the brief | FR-001 | — | Done 2026-11-01 |
| 2 | Draft the FRs | FR-002 | — | Not started |
| 3 | Draft the NFRs | NFR-PERF-01 | — | Not started |"""


def status(rows=PLAN_ROWS, waiting="nothing", phase="1 Requirements", review="Review after writing"):
    return textwrap.dedent("""\
        # STATUS: Demo

        | Field | Value |
        |---|---|
        | Code review mode | {review} |
        | Current phase | {phase} |

        ## Phase 1 plan
        | # | Work | Covers | Needs from the owner | Status |
        |---|---|---|---|---|
        {rows}

        ## Handoff
        - **Next action:** the next row
        - **Waiting on user:** {waiting}
        """).format(rows=rows.replace("\n", "\n        "), waiting=waiting, phase=phase, review=review)


# A stand-in for `claude -p`: marks the first "Not started" row Done, or follows FAKE_MODE.
FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
pathlib.Path("calls.log").open("a").write(json.dumps(args) + "\\n")
mode = os.environ.get("FAKE_MODE", "progress")
status = pathlib.Path("docs/sdlc/demo/STATUS.md")
text = status.read_text()
result = "Done.\\nAUTOPILOT-RESULT: continue"
if mode == "error":
    print(json.dumps({"is_error": True, "subtype": "error_during_execution", "result": "boom"}))
    sys.exit(0)
if mode == "crash":
    sys.exit(3)
if mode == "progress":
    if "| Not started |" in text:
        text = text.replace("| Not started |", "| Done |", 1)
    else:
        text = text.replace("**Waiting on user:** nothing", "**Waiting on user:** G1 sign-off")
if mode == "ask-stop":
    text = text.replace("| Not started |", "| Done |", 1)
    result = "AUTOPILOT-RESULT: stop needs a product decision"
status.write_text(text)
print(json.dumps({"result": result, "total_cost_usd": 0.5, "session_id": "s-1", "is_error": False,
                  "num_turns": 7, "usage": {"cache_read_input_tokens": 900, "output_tokens": 40}}))
"""


class AutopilotTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project = Path(self.tmp.name)
        self.workspace = self.project / "docs/sdlc/demo"
        self.workspace.mkdir(parents=True)
        self.fake = self.project / "fake-claude"
        self.fake.write_text(FAKE_CLAUDE.replace("/usr/bin/env python3", sys.executable, 1), encoding="utf-8")
        self.fake.chmod(0o755)

    def tearDown(self):
        self.tmp.cleanup()

    def write_status(self, text):
        (self.workspace / "STATUS.md").write_text(text, encoding="utf-8")

    def read_status(self):
        return (self.workspace / "STATUS.md").read_text(encoding="utf-8")

    def run_autopilot(self, *extra, mode="progress"):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "autopilot.py"), "--claude-bin", str(self.fake), *extra],
            cwd=self.project, capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin", "FAKE_MODE": mode},
        )

    def calls(self):
        log = self.project / "calls.log"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def test_runs_one_session_per_item_and_stops_at_the_gate(self):
        self.write_status(status())
        done = self.run_autopilot()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(len(self.calls()), 3)  # rows 2 and 3, then the gate review
        self.assertIn("Waiting on user: G1 sign-off", done.stdout)
        self.assertIn("#2: Draft the FRs", self.calls()[0][1])
        self.assertIn("no open row", self.calls()[2][1])
        log = (self.project / ".claude/autopilot/demo.jsonl").read_text().splitlines()
        self.assertEqual(len(log), 3)
        self.assertEqual(json.loads(log[0])["usage"], {"cache_read_input_tokens": 900, "output_tokens": 40, "turns": 7})
        self.assertTrue((self.workspace / "progress.html").is_file())
        self.assertIn("Progress dashboard:", done.stdout)

    def test_stops_before_starting_when_waiting_on_user(self):
        self.write_status(status(waiting="G1 sign-off"))
        done = self.run_autopilot()
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.calls(), [])
        self.assertIn("Waiting on user: G1 sign-off", done.stdout)

    def test_stops_on_a_blocked_row(self):
        self.write_status(status(rows=PLAN_ROWS.replace("| Not started |", "| Blocked: needs NFR targets |", 1)))
        done = self.run_autopilot()
        self.assertEqual(self.calls(), [])
        self.assertIn("Blocked: needs NFR targets", done.stdout)

    def test_stops_in_phase_4_when_code_is_approved_before_writing(self):
        self.write_status(status(phase="4 Implementation", review="Approve before writing"))
        done = self.run_autopilot()
        self.assertEqual(self.calls(), [])
        self.assertIn("Approve before writing", done.stdout)

    def test_refuses_a_template_plan(self):
        self.write_status(status(rows="| 1 | <e.g. Draft the brief and the FRs> | <IDs> | — | Not started |"))
        done = self.run_autopilot()
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.calls(), [])

    def test_stops_when_a_session_changes_nothing(self):
        self.write_status(status())
        done = self.run_autopilot(mode="no-op")
        self.assertEqual(done.returncode, 1)
        self.assertEqual(len(self.calls()), 1)
        self.assertIn("didn't change STATUS.md", done.stdout)

    def test_stops_on_a_session_error_or_crash(self):
        for mode in ("error", "crash"):
            with self.subTest(mode=mode):
                self.write_status(status())
                done = self.run_autopilot(mode=mode)
                self.assertEqual(done.returncode, 1)
                self.assertIn("Autopilot stopped", done.stdout)

    def test_stops_when_the_session_asks_to(self):
        self.write_status(status())
        done = self.run_autopilot(mode="ask-stop")
        self.assertEqual(len(self.calls()), 1)
        self.assertIn("needs a product decision", done.stdout)

    def test_honours_max_sessions_and_budget(self):
        self.write_status(status())
        self.run_autopilot("--max-sessions", "1")
        self.assertEqual(len(self.calls()), 1)
        self.write_status(status())
        (self.project / "calls.log").unlink()
        done = self.run_autopilot("--budget-usd", "0.4")
        self.assertEqual(len(self.calls()), 1)  # the first session costs 0.5
        self.assertIn("--max-budget-usd", self.calls()[0])
        self.assertIn("Reached --budget-usd", done.stdout)

    def test_dry_run_starts_nothing_and_denies_push(self):
        self.write_status(status())
        done = self.run_autopilot("--dry-run")
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.calls(), [])
        self.assertIn("--disallowedTools", done.stdout)
        self.assertIn("'Bash(git push*)'", done.stdout)
        self.assertIn("react-webapp-skill:react-webapp-sdlc", done.stdout)
        self.assertFalse((self.workspace / "progress.html").exists())

    def test_passes_effort_only_when_set(self):
        self.write_status(status())
        self.assertNotIn("--effort", self.run_autopilot("--dry-run").stdout)
        self.assertIn("--effort high", self.run_autopilot("--dry-run", "--effort", "high").stdout)


class StatusParserTest(unittest.TestCase):
    def test_next_plan_row(self):
        row = next_plan_row(status())
        self.assertEqual((row["number"], row["work"], row["needs"], row["status"]),
                         ("2", "Draft the FRs", "—", "Not started"))
        self.assertIsNone(next_plan_row(status(rows="| 1 | Brief | FR-001 | — | Done |")))
        self.assertIsNone(next_plan_row("# no plan"))

    def test_handoff_field(self):
        self.assertEqual(handoff_field(status(waiting="G1 sign-off"), "Waiting on user"), "G1 sign-off")
        self.assertEqual(handoff_field("## Handoff\n- **Next action:** x\n", "Waiting on user"), "")


if __name__ == "__main__":
    unittest.main()
