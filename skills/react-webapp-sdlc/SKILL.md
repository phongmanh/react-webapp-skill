---
name: react-webapp-sdlc
description: Waterfall lifecycle for building a React + TypeScript web app or feature - requirements, architecture, detailed design, implementation, testing, release to hosting and maintenance - with phase gates, sign-offs, traceability and change control. Bundles web best practices (feature-based architecture, Vite + React 19, React Router, TanStack Query, Zod, React Hook Form, Tailwind CSS, OWASP ASVS security, WCAG 2.2 AA accessibility, Core Web Vitals performance, Vitest + Testing Library + MSW + Playwright testing), canonical TypeScript code patterns, a default design style, a PR review checklist and deliverable templates (requirements, architecture, ADR, feature design, test plan, release checklist). Use when planning, designing, building, testing or releasing a React/TypeScript web app or feature phase by phase, when writing any of those documents for a React project, or when the user mentions waterfall, SDLC, V-model or phase gates for a web app, or when the user wants the workflow to run unattended (autopilot), one fresh session per task.

---

# React web app SDLC (waterfall)

A gated, document-driven lifecycle for building a React + TypeScript web app, or a feature in an existing one. Each phase produces reviewed deliverables and ends at a gate. The next phase starts only after an explicit sign-off.

## Principles
- **Quality is designed in.** Each design phase writes the tests that later verify it (see the [V-model](#v-model)). Every NFR has a measurable target.
- **Traceable.** Every requirement has an ID that is carried into design, code, tests and the release ([RTM](templates/rtm.md)).
- **Gates are real.** A baselined deliverable changes only through a [change request](templates/change-request.md).
- **Opinionated defaults, explicit deviations.** The [default stack](reference/architecture.md#default-stack) applies unless an ADR says otherwise.
- **Project rules win.** If the target repo has a `CLAUDE.md`, `.claude/rules/` or its own lint and format config, they override this skill's conventions. This skill still governs the process and the quality bars.
- **Proportionate depth.** Write as much as the risk needs. A feature gets lighter documents than a new app; see [Tailoring](#tailoring-app-vs-feature).
- **Reviewable output.** Documents follow fixed templates. Code follows one [pattern per concern](reference/code-patterns.md). PRs are small and single-purpose ([review checklist](reference/review-checklist.md)).

## Lifecycle
| # | Phase | Key question | Main deliverables | Gate |
|---|---|---|---|---|
| 1 | [Requirements](phases/1-requirements.md) | What must the app do, and how well? | Requirements (brief, FRs, NFRs, browsers and devices, data inventory), acceptance outline, RTM | G1 Requirements baseline |
| 2 | [Architecture](phases/2-architecture.md) | How is the app structured, and on which stack? | Architecture document, ADRs, threat model, master test plan | G2 Architecture baseline |
| 3 | [Detailed design](phases/3-detailed-design.md) | How is each feature built? | Feature designs (routes, screens, state, contracts, PR plan), integration and E2E test cases | G3 Ready to build |
| 4 | [Implementation](phases/4-implementation.md) | Is it built right? | Code and unit tests, CI quality gates, release candidate | G4 Code complete |
| 5 | [Testing](phases/5-testing.md) | Does it meet the spec in real browsers? | Test reports, UAT sign-off, test summary report | G5 Release readiness (go/no-go) |
| 6 | [Release](phases/6-release.md) | Is it live, and stable? | Release checklist, rollout record, handover | G6 Launch accepted |
| 7 | [Maintenance](phases/7-maintenance.md) | Does it stay healthy as browsers, dependencies and the backend change? | Health reviews, CRs, hotfixes, dependency and runtime updates | Mini-cycle per change |

## V-model
| Design phase | Verified in Phase 5 by | Test basis written in |
|---|---|---|
| 1 Requirements | Acceptance tests (UAT on the staging or preview deployment) | Phase 1: acceptance outline |
| 2 Architecture | System and NFR tests on the browser matrix: Core Web Vitals, bundle size, security headers, accessibility, offline, upgrade | Phase 2: master test plan |
| 3 Detailed design | Integration tests (components with real hooks and MSW) and Playwright E2E flows | Phase 3: feature designs |
| 4 Implementation | Unit tests (schemas, hooks, helpers) | Phase 4: written with the code |

## Tailoring: app vs feature
| Deliverable | New app | Feature in an existing app |
|---|---|---|
| [Requirements](templates/requirements.md) | Full | Brief, feature FRs, changed NFRs, new data and third-party scripts |
| [Architecture](templates/architecture.md) | Full, with stack and layout ADRs | Delta: changed features, data flows and threats |
| [ADRs](templates/adr.md) | Stack deviations, project layout, other key choices | One per significant decision |
| [Feature design](templates/feature-design.md) | One per feature | One for the feature |
| [Test plan](templates/test-plan.md) | Master plan and summary report | Feature scope plus regression scope |
| [Release checklist](templates/release-checklist.md) | Full, with hypercare | Standard; release behind a feature flag |
| [STATUS](templates/status.md), [RTM](templates/rtm.md) | Required | Required (feature rows only) |

A small feature may combine G2 and G3 into one review. **G5 is never skipped or combined.**

## How Claude runs this workflow
1. **Workspace.** In the target project, find `docs/sdlc/<initiative-slug>/STATUS.md`. If it exists, resume from its `## Handoff`; the SessionStart hook already shows it with the phase and the next plan row, so read only the STATUS.md sections the task needs (the gate log, the current plan, open items). If not, create it from [templates/status.md](templates/status.md).
2. **Facts.**
   - In an existing web project, read `package.json`, the lockfile type, `tsconfig*.json`, `vite.config.*` (or the framework config), the lint and format config, `.nvmrc`, `CLAUDE.md` and `.claude/rules/`. Record the framework, the router, the data layer, the styling approach and the Node version in STATUS.md. Don't contradict them without an ADR.
   - When a backend, an API contract or a design already exists, read them as inputs:
     - the contract (e.g. OpenAPI);
     - the backend's own requirements, and the rules it sets for clients (auth, CORS, rate limits, headers, versioning);
     - every screen of the design.

     Save a copy of each, with its source and version, under the workspace's `inputs/`, so later sessions don't re-fetch it. Record each source in STATUS.md. Cite upstream IDs with a prefix (e.g. `BE-FR-003`), so they don't clash with the app's own, and fill the RTM's **Upstream source** column.
3. **Scope.** Confirm with the user:
   - new app or feature;
   - target users, their devices and browsers;
   - compliance (e.g. GDPR, CCPA, HIPAA, PCI DSS) and the ASVS level;
   - rendering needs: a client-side SPA, or SEO and server rendering (which changes the stack, see [architecture](reference/architecture.md#when-to-deviate));
   - existing documents to reuse;
   - how the owner reviews code in Phase 4: approve each PR's code before it's written, or review each PR after it's written.

   Record the answers and pick the tailoring column.
4. **Load only what's needed:** the current phase file and the references its **Load** line lists. If STATUS.md doesn't show the previous gate as approved, stop and say so.
   Read the workspace's documents and inputs the same way. For any file over about 24 KB (STATUS.md, designs, the architecture, contracts), read only the sections the Handoff's **Load** names, by line range; the plugin's Read hook refuses any Read of more than 24 KB under `docs/sdlc/`, whole file or range, and returns the file's outline with line numbers. Reading a whole architecture, design or contract file costs every later call in the session.
5. **Write the deliverables** from `templates/` into the workspace.
   - Mark unknowns `TBD-<n>` and assumptions `ASSUMPTION:`, and list them in STATUS.md.
   - Ask the user for what only stakeholders can decide: targets, priorities, approvers.
   - Never invent requirements, numbers, approvals or sign-offs.
   - Mark any number Claude suggests (an NFR target, a budget) as **(proposed)**. Confirming those numbers is a TBD that blocks G1.
6. **Trace.** Add every new requirement, design element and test to `rtm.md`, all in one edit (or one Write) rather than one edit per row.
7. **Gate review.** Run the phase's exit checklist. Present the deliverables and their status, the checklist results, open TBDs, top risks, and a recommendation: approve, approve with conditions, or rework.
8. **STOP for sign-off.** Ask for the decision and the approver's name and role. Record both in the STATUS.md gate log and suggest a git tag (`sdlc/<slug>/G<n>`). A waiver records the accepted risk and who accepted it.
9. **After a baseline,** every change to an approved deliverable goes through a [change request](templates/change-request.md): RTM impact analysis → decision → update the affected deliverables → re-check the affected gates.
   Once the gate decision is in the gate log, move that phase's `## Phase <n> plan` and its `## G<n> review` to `STATUS-archive.md` in the workspace. STATUS.md is read every session, so it holds only what is current.
10. **End of session.** Finish one unit of work per session. Before stopping, update the deliverable, its row in STATUS.md's current `## Phase <n> plan`, and rewrite the `## Handoff` section from the template. Group the STATUS.md changes into as few edits as you can: by now the context is at its largest, and every tool call re-sends all of it. In [autopilot](#autopilot) the next session starts on its own, so don't tell the user to `/clear`.
    The plugin's hook rewrites `progress.html` after every STATUS.md edit, so it shows as changed in `git status`; that change is expected and needs no check.

**Partial use.** If the user wants a single deliverable (e.g. "write the feature design for sign-in"), produce just that one, following its phase's guidance. Mention any missing upstream inputs, but don't force the whole lifecycle.

Workspace layout in the target project:
```
docs/sdlc/<initiative-slug>/
├── STATUS.md               # phase, gate log, decisions, risks, CRs, open items
├── requirements.md         # Phase 1
├── rtm.md                  # Phases 1–6
├── architecture.md         # Phase 2 (threat model inside)
├── adr/NNNN-<decision>.md  # Phase 2 onwards
├── design/<feature>.md     # Phase 3
├── test-plan.md            # Phases 1–5 (+ test summary report)
├── release-checklist.md    # Phase 6
├── inputs/                 # cached external sources (contracts, design exports)
├── cr/CR-NNN-<title>.md    # after any baseline
└── postmortem/PM-NNN-<title>.md  # Phase 7, after each S1 incident
```
The app itself lives in the project root (or the package the architecture names), next to `docs/`.

## Autopilot
Unattended mode: a driver script starts a fresh headless session (`claude -p`) for each row of the current phase plan, and the SessionStart hook hands each one the handoff. Nobody answers questions in these sessions. **Gates still stop:** autopilot never records a gate decision.

**Starting it** (interactive session, when the user asks for autopilot):
1. Check that Scope (step 3) is done and STATUS.md has a `## Phase <n> plan` with real rows. If not, do those first, with the user.
2. In Phase 4, **Code review mode** must be *Review after writing*. *Approve before writing* needs the owner for every PR, so autopilot refuses it.
3. Run, from the project root, with Bash `run_in_background`: `python3 <this skill's base directory>/../../scripts/autopilot.py --workspace docs/sdlc/<slug>`. Use `--dry-run` first to show the user the command. Options: `--model` and `--effort` (default: Claude Code's), `--max-sessions` (default 20), `--budget-usd`, `--session-timeout` (minutes).
4. Tell the user it stops by itself when it needs them, that `TaskStop` (or Ctrl-C) stops it early, and that each session is logged in `.claude/autopilot/<slug>.jsonl`.

**The driver stops when:** the Handoff's **Waiting on user** isn't "nothing"; the next plan row is `Blocked`; a session fails, changes nothing in STATUS.md, or ends with `AUTOPILOT-RESULT: stop`; or the session or budget cap is reached. It denies `git push`, `gh`, merges, rebases, hard resets and `AskUserQuestion`; the baseline gate's confirm becomes a denial.

**Inside an autopilot session** (the prompt says AUTOPILOT):
- Do exactly one plan row, then the End of session step (10). If the plan has no open row: when the gate log approves the current phase's gate, set the next phase in STATUS.md and write its `## Phase <n> plan`; otherwise run the gate review (step 7).
- **Large rows:** split by content, not by how the session feels. A row that writes a whole feature design does §1–§5, saves them, leaves the row `In progress`, puts §6–§10 and the RTM in the Handoff's **Next action**, and ends with `AUTOPILOT-RESULT: continue`. Stop the same way in any phase once you have written about 24 KB of one deliverable.
- **Cut-off sessions:** if `git status` shows work the Handoff doesn't mention (an earlier session may have been cut off), continue from it instead of starting the row over.
- **Never ask.** Anything only the owner can decide (step 5) becomes an Open item; set the row to `Blocked: <reason>` and **Waiting on user** to the decision, then stop. **(proposed)** numbers stay proposed.
- **Gate row:** run the exit checklist and write the gate review (checklist results, open TBDs, top risks, recommendation) as a `## G<n> review` section just above the Handoff. Set **Waiting on user** to `G<n> sign-off`. Never write the gate log or a tag.
- **Baselines:** never edit an Approved deliverable. A needed change becomes a draft CR, and the row is Blocked on its approval.
- **Phase 4:** one PR row per session. Create its branch (`feature/<ticket-id>-<desc>`, per the project's git rules) from the current HEAD, so it stacks on the previous unmerged PR. Implement it, run `npm run check` (and the project's own pre-merge checks), fix what fails, then update the RTM and STATUS.md and commit them with the code, citing the ticket and FR IDs. Install only the dependencies the approved architecture lists; a new one is a CR. If the checks can't be made green, commit nothing and set the row Blocked. Never push, deploy or open a PR: the user does, and reviews each one.
- **Last line of the reply:** `AUTOPILOT-RESULT: continue`, or `AUTOPILOT-RESULT: stop <reason>` when the next session can't make progress without the user.

## File index
- **Phases:** [1 Requirements](phases/1-requirements.md) · [2 Architecture](phases/2-architecture.md) · [3 Detailed design](phases/3-detailed-design.md) · [4 Implementation](phases/4-implementation.md) · [5 Testing](phases/5-testing.md) · [6 Release](phases/6-release.md) · [7 Maintenance](phases/7-maintenance.md)
- **Reference:**
  - [architecture](reference/architecture.md): layers, project layouts, default stack, state placement, error model;
  - [project setup](reference/project-setup.md): scaffolding, config files, scripts, CI and hosting;
  - [code patterns](reference/code-patterns.md): canonical TypeScript and React for each layer;
  - [UI/UX](reference/ui-ux.md) · [design style](reference/design-style.md) · [security & privacy](reference/security-privacy.md) · [performance & reliability](reference/performance-reliability.md) · [testing](reference/testing.md) · [review checklist](reference/review-checklist.md).
- **Templates:** [status](templates/status.md) · [requirements](templates/requirements.md) · [architecture](templates/architecture.md) · [adr](templates/adr.md) · [feature-design](templates/feature-design.md) · [test-plan](templates/test-plan.md) · [release-checklist](templates/release-checklist.md) · [change-request](templates/change-request.md) · [rtm](templates/rtm.md) · [postmortem](templates/postmortem.md)

## Conventions
- **Requirement IDs.** `FR-nnn` for functional requirements. `NFR-<ATTR>-nn` for non-functional ones, where ATTR is one of PERF, REL, SEC, PRIV, A11Y, MAINT, TEST, COMPAT, OBS, I18N, SIZE.
- **Test IDs.** `UT-` unit, `IT-` integration (components with MSW), `UI-` Playwright E2E, `ST-` system/NFR, `AT-` acceptance. Every test title starts with its ID, so the RTM can be checked with `grep`.
- Commits, PRs, designs and tests cite these IDs.
- **Numbers marked "e.g."** are examples. The real targets are agreed in the requirements.
- **Versions.** Dependencies are always the latest stable release, recorded once in `package.json` with a committed lockfile; this skill pins none. Node is an LTS line pinned in `.nvmrc`. Tools move fast: when a step here no longer matches a tool's current docs, follow the docs and note the change in the PR.
