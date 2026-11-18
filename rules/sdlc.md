---
paths:
  - "docs/sdlc/**"
---
# SDLC Documents

Applies to the deliverables of the react-webapp-sdlc workflow (`/react-webapp-skill:react-webapp-sdlc`) under `docs/sdlc/<initiative-slug>/`.

- **Start from `STATUS.md`.** Check the current phase, and confirm the previous gate is approved before writing a later phase's deliverable.
- **Follow the template** in the react-webapp-sdlc skill's `templates/`, keeping its section order and tables.
- **IDs everywhere:**
  - `FR-nnn`;
  - `NFR-<ATTR>-nn`, with the attributes the skill lists;
  - test IDs `UT-`/`IT-`/`UI-`/`ST-`/`AT-`, at the start of every test title.

  Every new requirement, design element and test gets an `rtm.md` row in the same change.
- **Never invent** numbers, approvals, approver names, sign-off dates or test results. Mark unknowns `TBD-<n>` and assumptions `ASSUMPTION:`, and list both in `STATUS.md`.
- **Baselined documents.** A deliverable whose `STATUS.md` row says Approved is baselined.
  - Change it only through an approved `cr/CR-NNN-<title>.md`.
  - The `guard-sdlc-baseline.py` hook asks the user to confirm before such an edit. Only the user can switch it off (`SDLC_GATE=off` in `.claude/settings.local.json`); the CR rule still holds when it's off.
- **Gate decisions** go only in the `STATUS.md` gate log, and only after the approver has given them in the conversation.
- **Autopilot** sessions (the skill's `## Autopilot` section) never record gate decisions, never edit baselined documents, never push and never deploy. When they need the owner, they set the plan row to `Blocked: <reason>` or the Handoff's **Waiting on user**, and stop.
- **Handoff.** `STATUS.md` ends with a `## Handoff` section, rewritten at the end of every session and never baselined. Facts only, ≤ 15 lines (the hook injects at most 30):
  ```markdown
  ## Handoff
  - **Last session:** <date> — <what got done, one line>
  - **State:** <e.g. "G1 awaiting sign-off" · "Phase 4 PR 6 (notes list) in review">
  - **Next action:** <the exact first step for the next session>
  - **Load:** <files and sections or line ranges to read first>
  - **Inputs:** <where external sources are cached or pinned, with versions and commits>
  - **Waiting on user:** <decision, approval or review, or "nothing">
  ```
- **Keep documents short:** tables and bullets over prose; link instead of repeating.
