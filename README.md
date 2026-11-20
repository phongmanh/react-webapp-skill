# react-webapp

A Claude Code plugin for building React + TypeScript web apps phase by phase, with a gated waterfall lifecycle: requirements, architecture, detailed design, implementation, testing, release and maintenance. Each phase produces reviewed deliverables from fixed templates, and the next phase starts only after an explicit sign-off.

## Install
```
/plugin marketplace add phongmanh/react-webapp-skill
/plugin install react-webapp@react-webapp
```

**Upgrading from 0.4 (`react-webapp-skill`)?** The plugin was renamed. Remove the old one first, or its hooks run twice next to the new ones:
```
/plugin uninstall react-webapp-skill@react-webapp-skill
/plugin marketplace remove react-webapp-skill
/plugin marketplace add phongmanh/react-webapp-skill
/plugin install react-webapp@react-webapp
```
Existing `docs/sdlc/` workspaces keep working as they are.

## Skills
| Skill | For | Run |
|---|---|---|
| `react-webapp` | A React + TypeScript web app or feature: feature-based architecture, Vite + React 19, React Router, TanStack Query, Zod, React Hook Form, Tailwind CSS, OWASP ASVS, WCAG 2.2 AA, Core Web Vitals, Vitest + Testing Library + MSW + Playwright, static hosting release | `/react-webapp` |
| `autopilot` | Running the current phase plan unattended, one fresh session per row, until it needs you | `/react-webapp:autopilot [slug]` |
| `progress` | Where the work stands: a short summary, plus a colorful dashboard page that opens in your browser | `/react-webapp:progress [slug]` |

Claude also picks `react-webapp` on its own when you ask it to plan, design, build, test or release a React web app or feature that way. It bundles phase guides, references (architecture, project setup, code patterns, UI/UX, a default design style, security and privacy, performance, testing, a PR review checklist) and deliverable templates.

The deliverables live in your project under `docs/sdlc/<initiative-slug>/`, with `STATUS.md` as the control file: phase, gate log, risks, change requests, the current phase plan and the session handoff.

## Hooks
| Hook | Event | What it does |
|---|---|---|
| `session-context.py` | `SessionStart` | For each `docs/sdlc/*/STATUS.md`, shows the current phase, the next open row of the newest `## Phase N plan` and the `## Handoff` section. A session can start after `/clear` and pick up where the last one stopped. |
| `guard-sdlc-baseline.py` | `PreToolUse` (`Edit`, `Write`, `MultiEdit`) | Asks you to confirm before Claude edits a deliverable that `STATUS.md` marks Approved. A baselined document changes only through an approved change request. |
| `guard-large-read.py` | `PreToolUse` (`Read`) | Refuses a read of more than 24 KB under `docs/sdlc/` (a whole large file, or a range that covers most of one) and returns its outline with line numbers, so Claude reads only the sections it needs. Everything read stays in the context and is re-sent on every later call. |
| `refresh-progress.py` | `PostToolUse` (`Edit`, `Write`, `MultiEdit`) | After Claude edits a `STATUS.md`, refreshes its progress dashboard, if you've created one. |

Only you can switch the baseline gate off, in your git-ignored `.claude/settings.local.json`:
```json
{ "env": { "SDLC_GATE": "off" } }
```

## Progress dashboard
Ask Claude "where are we?" or run:
```
/react-webapp:progress            # every workspace
/react-webapp:progress guest-web  # one workspace
```
You get a short summary in the chat, and `progress.html` opens in your browser: a colorful page with the phase timeline, gate decisions, the current phase plan with a progress ring, deliverables, a risk grid, open items, change requests and the handoff, with anything waiting on you highlighted. It follows your light or dark setting and works on a phone.

From then on the page keeps itself current: the `refresh-progress.py` hook rewrites it whenever Claude edits that `STATUS.md`, and autopilot refreshes it after each session. Keep it open and reload. Commit it or git-ignore `docs/sdlc/**/progress.html`, as your team prefers. The page is self-contained apart from its web fonts; offline, it falls back to system fonts.

Outside Claude Code, run the script from anywhere in your project: `python3 <plugin>/scripts/progress.py [<slug>] [--open]`.

**In another skill.** The dashboard reads the shape of `STATUS.md`, not anything web-specific, so other skills can use it too. It needs a `| Field | Value |` header table with a `Current phase` row starting with the phase number. These `##` sections are optional, and any that are missing are left out: `Deliverables`, `Gate log` (gates named `G<n> …`, one per phase), `Risks` (Likelihood and Impact as H/M/L), `Open items`, `Change requests`, `Phase <n> plan` (# · Work · … · Status) and `Handoff` (`- **Next action:**`, `- **Waiting on user:**`, …). Pass it the phase names with `--phases "Discovery,Build,Launch"` or `--skill-dir <your-skill>`, which reads its `phases/<n>-<name>.md` files.

## Autopilot
Runs the workflow unattended: `scripts/autopilot.py` starts a fresh headless session (`claude -p`) for each row of the current `## Phase N plan`, and the `session-context.py` hook hands each one the last handoff. Gates still stop: autopilot never records a sign-off.

Do scope and the first phase plan interactively, then run `/react-webapp:autopilot [slug]` (or ask Claude to "run autopilot"), or run it yourself from the project root. The script is in the installed plugin (`~/.claude/plugins/cache/react-webapp/react-webapp/<version>/scripts/`) or your clone of this repo:
```
python3 <plugin>/scripts/autopilot.py --workspace docs/sdlc/<slug> --dry-run
python3 <plugin>/scripts/autopilot.py --workspace docs/sdlc/<slug> --budget-usd 20
```

| It stops when | Then you |
|---|---|
| The Handoff's **Waiting on user** isn't "nothing" (e.g. `G1 sign-off`, a decision, a CR approval) | Decide or sign off in an interactive session, set it back to "nothing", re-run |
| The next plan row is `Blocked: <reason>` | Unblock it, re-run |
| Phase 4 with code review mode *Approve before writing* | Switch to *Review after writing*, or continue interactively |
| A session fails, changes nothing in STATUS.md, or ends with `AUTOPILOT-RESULT: stop` | Read the reason and the log |
| `--max-sessions` (default 20) or `--budget-usd` is reached | Re-run when ready |

- **Permissions.** Sessions run with `--permission-mode acceptEdits` and allow file tools, `npm run`, `npm ci`, `npm install`, `npm ls`, `npm audit`, `npm create vite@latest`, `npx playwright install`, `node`, scaffolding helpers (`mkdir`, `cp -Rn`, `rm -rf .scaffold`) and local git (`status`, `diff`, `log`, `branch`, `switch`, `checkout -b`, `add`, `commit`). They deny `git push`, merges, rebases, hard resets, `gh` and `AskUserQuestion`. The baseline gate's confirm becomes a denial. Your project's `.claude/settings.json` allow list still applies.
- **Dependencies.** Sessions install only what the approved architecture lists; a new dependency is a change request.
- **Phase 4.** One branch and commit per PR row, stacked on the previous one after `npm run check` passes. You push, open and review the PRs, and you deploy.
- **Dashboard.** `progress.html` in the workspace is refreshed after each session; `--no-dashboard` turns that off.
- **Log.** One JSON line per session (time, session ID, plan item, cost, result) in `.claude/autopilot/<slug>.jsonl`; consider git-ignoring `.claude/autopilot/`.

## Optional: the SDLC rule
Plugins can't ship rule files. `rules/sdlc.md` restates the document rules (IDs, baselines, gate decisions, handoff format) and loads only while Claude edits `docs/sdlc/**`. To use it, copy it into your project as `.claude/rules/sdlc.md`.

## Development
Run the hook and autopilot tests from the repo root:
```
python3 -m unittest discover -s hooks/test
python3 -m unittest discover -s scripts/test
```
Check the plugin and the marketplace with `claude plugin validate .`.

## License
MIT. See [LICENSE](LICENSE).
