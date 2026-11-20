# STATUS: <Initiative name>

> The control file for the react-webapp-sdlc workflow. Claude reads it first to resume work.
>
> Keep it current. It's the single place for gate decisions, risks and open items.

| Field | Value |
|---|---|
| Initiative | <name> (`docs/sdlc/<initiative-slug>/`) |
| Skill | react-webapp-sdlc |
| Type | New app / Feature in <app> |
| App location | e.g. repository root, or `apps/web/` |
| Stack | e.g. Vite + React 19 + TypeScript · React Router · TanStack Query · Tailwind (ADR-<n> for deviations) |
| Node | e.g. 24 LTS (`.nvmrc`) |
| Project layout | One package with feature folders / Workspace monorepo (ADR-<n>) |
| Rendering | Client-side SPA / SSR or SSG (ADR-<n>) |
| Security level | ASVS L1 / L2 |
| Compliance | e.g. GDPR, ePrivacy, CCPA, WCAG 2.2 AA |
| Product owner / Tech lead | <name, role> / <name, role> |
| Inputs | e.g. backend contract `inputs/openapi.yaml` v<x>, design `<link>` (or "none") |
| Code review mode | Approve before writing / Review after writing (each PR) |
| Current phase | 1 Requirements |
| Tailoring | Full (app) / Light (feature) |
| Last updated | YYYY-MM-DD |

## Deliverables
| Phase | Deliverable | File | Status (Not started / Draft / In review / Approved) | Version |
|---|---|---|---|---|
| 1 | Requirements | requirements.md | Not started | — |
| 1–6 | RTM | rtm.md | Not started | — |
| 2 | Architecture + threat model | architecture.md | Not started | — |
| 2+ | ADRs | adr/NNNN-<decision>.md | — | — |
| 1–5 | Test plan + summary report | test-plan.md | Not started | — |
| 3 | Feature designs | design/<feature>.md | Not started | — |
| 6 | Release checklist | release-checklist.md | Not started | — |

## Gate log
Decision is one of: Approved / Approved with conditions / Rejected / Waived.

| Gate | Date | Decision | Approver (name, role) | Conditions or accepted risk | Tag |
|---|---|---|---|---|---|
| G1 Requirements baseline | | | | | |
| G2 Architecture baseline | | | | | |
| G3 Ready to build | | | | | |
| G4 Code complete | | | | | |
| G5 Release readiness | | | | | |
| G6 Launch accepted | | | | | |

## Decisions
| Date | Decision | Recorded in (ADR / minutes) |
|---|---|---|

## Risks
| ID | Risk ("If …, then …") | Likelihood (H/M/L) | Impact (H/M/L) | Owner | Mitigation | Status |
|---|---|---|---|---|---|---|
| R-01 | | | | | | Open |

## Change requests
| CR ID | Title | Status | Affected items | Decision date |
|---|---|---|---|---|

## Open items
A TBD that blocks a Must requirement blocks the gate.

| ID | Type (TBD / ASSUMPTION / Question) | Description | Blocks gate? | Owner | Status |
|---|---|---|---|---|---|

## Phase 1 plan
One row per unit of work, each sized for one session: in Phase 3, half a feature design per row (§1–§5, then §6–§10 and the RTM); one row only for a design that will stay under about 24 KB. Start a new `## Phase <n> plan` table when a phase starts; the SessionStart hook reads the newest one and shows its first row that isn't Done. Status is one of: Not started / In progress / Done / Blocked: <reason>. Autopilot stops at a Blocked row.

| # | Work | Covers | Needs from the owner | Status |
|---|---|---|---|---|
| 1 | <e.g. Draft the brief and the FRs> | <IDs> | <decision or input, or —> | Not started |

## Handoff
<!-- Keep this the last section. Rewritten at the end of every session, never baselined. Facts only, ≤ 15 lines. -->
- **Last session:** YYYY-MM-DD — <what got done, one line>
- **State:** <e.g. "G1 awaiting sign-off">
- **Next action:** <the exact first step for the next session>
- **Load:** <the few sections the next action needs first, with line ranges, e.g. `design/menu.md` §2 public API (L232–300); not other features' internals>
- **Inputs:** <where external sources are cached or pinned, with versions and commits, or "none">
- **Waiting on user:** <decision, approval or review, or "nothing">
