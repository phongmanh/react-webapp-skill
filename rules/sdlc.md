---
paths:
  - "docs/sdlc/**"
---
# SDLC Documents

Applies to the deliverables of the react-webapp workflow (`/react-webapp`) under `docs/sdlc/<initiative-slug>/`.

- **Start from `STATUS.md`.** Check the current phase, and confirm the previous gate is approved before writing a later phase's deliverable.
- **Follow the template** in the react-webapp skill's `templates/`, keeping its section order and tables.
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
  - **Load:** <the few sections the next action needs first, with line ranges; for another feature, its §2 public API, not its internals>
  - **Inputs:** <where external sources are cached or pinned, with versions and commits>
  - **Waiting on user:** <decision, approval or review, or "nothing">
  ```
- **Keep documents short, because every later session re-reads them:** a feature design is read by each feature that depends on it, so its size is paid many times. Aim for a feature design that fits one Read (about 24 KB, the read hook's limit); detail only Phase 4 needs belongs in the code. Other features depend on a design's §2 public API only, so keep that section self-contained and read only it from designs you depend on. Keep to the template's sections and give each fact once. Cite another document by section (`architecture.md §5.4`) instead of restating it. Write signatures and types, not full implementations; the code holds those in Phase 4. Use one table row per case, without paragraphs around it.
