# UI/UX reference

How user experience is decided, written down, built and verified across the phases. The visual language (tokens, components, shells) is in [design-style.md](design-style.md); this file covers the process and the patterns. The rule is the same as for code: UX decisions are made once, in writing, before Phase 4, and every screen traces to the FRs it serves.

| Phase | UX work | Where it lands |
|---|---|---|
| 1 | Users, tasks, devices, inputs (design boards, sibling apps), UX NFRs | `requirements.md` brief, FRs, NFRs |
| 2 | Visual design (house style or brand), shells, breakpoints, navigation model | `architecture.md` cross-cutting and visual design |
| 3 | Screen inventory, flows, screen specs, UX states, microcopy | `design/<feature>.md` |
| 4 | Build to the spec; per-screen UX checklist | code, PR description |
| 5 | UX verification | test summary report |

## Phase 1: what the UX must achieve
- **Who and where.** Each role's main tasks, how often, and on what device: e.g. field staff on a phone, a shared wall tablet, back-office users on a laptop. This sets the breakpoints and the target sizes.
- **Inputs.** Existing design boards, a sibling app to match, or a brand. Save copies in the workspace's `inputs/` with their source and version. With no brand or sibling app, the default is [design-style.md](design-style.md) with the theme that fits the users (light shell or dark shell).
- **UX NFRs, measurable.** Defaults to offer: WCAG 2.2 AA (axe: zero violations on every route, plus a keyboard-only pass of the core flows); targets ≥ 44 × 44 px; usable from 360 px wide with no horizontal page scroll; the languages and the default one; "a first-time user completes <core task> without help", checked in the Phase 5 walkthrough.
- **Content.** Languages, tone, who writes the copy, and any wording the acceptance criteria must fix exactly.

Write acceptance criteria in user-visible terms (what appears, what's announced, where focus goes), so Phases 3 and 5 can trace them.

## Phase 3: screen inventory and flows
1. **Screen inventory.** The feature design's route table is the inventory: one row per screen with its FRs, auth, and layout (`public`, `shell`, `shell + side panel`, `dialog`). Every FR appears on at least one screen.
2. **Flows.** For each core task, a short numbered flow: entry point → screens and dialogs → success state → where the user lands. Mark branches for errors and permissions. Each flow becomes a `UI-` Playwright test.
3. **Navigation.** The nav items per role, their order, and the current-item rule. Deep links (every list filter and detail view has a URL), and what Back does.

## Screen specs
Every screen in the inventory gets a short spec in its feature design:

| Field | Content |
|---|---|
| Purpose | One sentence: the task it serves (FR IDs) |
| Primary action | The one filled primary button, or "none (read only)" |
| Layout | Shell, max width, columns per breakpoint, what moves or collapses below `lg` |
| Content order | Header → notices → filters → content → secondary actions, top to bottom |
| States | Loading, empty, error, success, offline, and permission-limited |
| Focus | Where focus goes on arrival, after submit, after an error, after a dialog closes |
| Copy | The fixed strings the acceptance criteria require, by catalogue key |

When design boards exist, cite the board per screen and record every intentional difference from it.

## Every screen has every state
| State | Show | Next action |
|---|---|---|
| Loading | `<output>` text or a skeleton at the final size, after a short delay so fast loads don't flash | — |
| Empty | A short explanation of why it's empty | A primary call to action (e.g. "Create note") |
| Error | A plain-language message from the `AppError` mapping, in an `Alert` or `ErrorPanel` | Retry, or sign in again for auth errors |
| Offline | Cached content plus a non-blocking notice (`role="status"`) | Retry automatically when the connection returns |
| Partial failure | The content, with an inline error for the part that failed | Retry that part |
| Permission-limited | What the user can see, without actions they can't take, and who to ask | — |

## Patterns
Use these unless a requirement says otherwise. Each has a primitive in [design-style.md](design-style.md) §5.

| Situation | Pattern |
|---|---|
| Lists of records | A table with a name link per row, filters above it bound to the URL, "Load more" (cursor paging) that moves focus to the first new row, and an empty state that says why and offers the next action |
| List + detail | Detail as a nested route: a side panel at ≥ 1280 px, its own page below (one URL, two layouts) |
| Create and edit | A full page for long forms, a `Dialog` for ≤ 4 fields. Errors on blur and on submit; focus the first invalid field. An unsaved-changes guard on long forms |
| Destructive actions | A `ConfirmDialog` that names the object and the effect; the confirm button repeats the verb; focus starts on Cancel. Irreversible ones (erase) require typing a word. For reversible ones, prefer Undo |
| Writes | The button shows pending and is disabled while in flight; success is announced in the polite live region; stale data (`412`) shows a notice and keeps the input; rate limits show a countdown |
| Secrets shown once | A read-only field + Copy (fallback: select the text and announce it) + "Shown once" and the expiry |
| Status | A badge with text ([design-style.md](design-style.md) §2.3); unknown values read "Other" with no actions |
| Background state | App-wide notices above `main` (`role="status"`): offline, new version available, account restrictions |
| Errors | Field errors next to the field; request errors in an `Alert` with Retry; route crashes in that route's error boundary, so the shell keeps working |

## Layout and navigation
- **Mobile-first and responsive.** Verify at 360, 768, 1024 and 1440 px. No horizontal page scroll; wide tables scroll inside their own wrapper.
- **Landmarks:** `header`, `nav`, `main`, `footer`; one `h1` per page; headings in order.
- **Skip link** ("Skip to content") as the first focusable element.
- **Route changes** move focus to the page's `h1` (or announce the change) and update `document.title`.
- **Browser history is navigation.** Back and Forward work through every flow; dialogs and filters that change the URL push or replace history deliberately.
- **One primary action per screen.**

## Accessibility (WCAG 2.2 AA)
- **Semantic HTML first:** `<button>` for actions, `<a href>` for navigation, real lists and tables, `<output>` for status text. ARIA only when no native element fits.
- **Keyboard:** everything interactive is reachable and operable by keyboard, in visual order, with a visible `:focus-visible` style. Never a positive `tabindex`; no keyboard traps.
- **Dialogs** use native `<dialog>` with `showModal()` (or a vetted primitive): focus moves in, Escape closes, focus returns to the trigger.
- **Labels.** Every control has a visible label; icon-only buttons have an accessible name from the catalogue. Decorative images use `alt=""`.
- **Targets** are at least 24 × 24 px (WCAG 2.2), and 44 × 44 px in the house style.
- **Contrast** is at least 4.5:1 for text, and 3:1 for large text, UI parts and focus indicators. Never use colour alone to convey meaning.
- **Zoom and reflow:** usable at 200% zoom, and reflows without loss at 320 CSS px (400%). Text uses `rem`; containers never get fixed heights.
- **Announcements.** Important changes (errors, saved, new results) go through a live region, never through animation alone. Honour `prefers-reduced-motion`.

## Text and localisation
- **Strings.** All user-facing text lives in the catalogue, in every supported language; a unit test checks that the catalogues have the same keys.
  - Plurals use `Intl.PluralRules` (or the i18n library's plural support).
  - Use placeholders, never string concatenation.
- **Formats.** `Intl.DateTimeFormat`, `Intl.NumberFormat` and `Intl.RelativeTimeFormat` for the user's locale. Store times in UTC; display them in local time.
- **Layout.** Translated text often runs 30–40% longer than English. Never size widths to English copy; let labels wrap. For RTL, use logical properties (`ms-*`, `me-*`, `start`, `end`) and set `dir` on `<html>`.
- **Copy** is short and specific: say what happened and what the user can do. Example: "No connection. Showing saved notes."

## Feedback and forms
- **Confirmations.** Announce success in the live region or with a toast that doesn't steal focus.
- **Validation.** Validate a field when the user leaves it and on submit, and show the error under the field. Disable the submit button only while a submit is in flight.
- **Long actions.** Show progress on the button and prevent double submits.
- **Autocomplete.** Set `autocomplete`, `type` and `inputmode` on fields, so password managers and mobile keyboards help.

## Phase 4: per-screen UX checklist
- [ ] Matches its screen spec: primary action, content order, layout per breakpoint.
- [ ] Only tokens and the shared primitives; no hex values, no one-off button or field styles.
- [ ] Loading, empty, error, success, offline and permission-limited states render, each with its specified copy.
- [ ] Focus lands where the spec says on arrival, after submit, after an error and after a dialog closes.
- [ ] Every control is ≥ 44 px, labelled, and reachable by Tab in visual order.
- [ ] Status never relies on colour alone.
- [ ] Copy comes from the catalogue in every language; the longest language wraps without clipping at 360 px.
- [ ] Tried at 360 px and 1440 px in `npm run dev`.

## Phase 5: UX verification
| Check | Method | Evidence |
|---|---|---|
| Automated accessibility | axe in Playwright on every route and every open dialog, all browsers | Violations per route (target 0) |
| Keyboard | A manual pass of each core flow with Tab, Shift+Tab, Enter, Space, Escape | Pass/fail per flow, notes |
| Screen reader smoke | VoiceOver or NVDA on sign-in and one core flow: names, roles, announcements | Pass/fail, notes |
| Responsive | Playwright at 360, 768, 1024 and 1440 px: no horizontal page scroll, the shell switches at `lg` | Pass/fail per viewport |
| Zoom and reflow | 200% zoom; 320 px reflow | Pass/fail per route |
| Visual consistency | Screenshots of each screen per viewport against the boards or the house style | Screenshots; differences logged as defects or accepted |
| Content | Every supported language on every screen: no missing keys, no clipped text | Pass/fail per language |
| Task walkthrough | The user (or a stand-in) does each core task without help | Completed / where they got stuck |

A UX defect is a defect like any other. A fix that changes a screen spec, a flow or a token is a CR.
