# Review checklist

For authors before they ask for a review, and for reviewers. A PR that breaks the PR rules goes back to the author before anyone reviews it line by line.

## PR rules
- **Small and single-purpose.** One concern, ≤ ~400 changed lines (not counting the lockfile and generated files), taken from the feature design's slice plan.
- **Branch and title** follow the project's git rules, e.g. `feature/JIRA-123-notes-list` and `feat(notes): add notes list (FR-001)`.
- **The description** covers:
  - what changed and why;
  - the FR IDs;
  - how it was tested;
  - for UI changes, screenshots at 360 px and 1440 px, and of each new state;
  - risks, and how to roll back (e.g. a feature flag).
- **CI is green before review,** and the PR has no unrelated reformatting.

## Review order
Feature design → tests (do they describe the right behaviour?) → schemas and contracts → data hooks → components → routes, catalogue keys and config.

## Checklist
**Scope and traceability**
- [ ] Matches the approved feature design; nothing unrequested; any deviation has an approved CR
- [ ] FR IDs in the PR; RTM row updated; test titles carry their IDs

**Architecture**
- [ ] Layer rules hold: no `fetch` in components; features import each other only through `index.ts`; `components/ui` and `lib` don't import features
- [ ] State lives in the right place: server state in TanStack Query (not copied into `useState`), filters and paging in the URL, forms in React Hook Form
- [ ] No new runtime dependency outside the architecture

**TypeScript**
- [ ] No `any`, `@ts-ignore` or unexplained `!`; external data parsed by a schema; types inferred from schemas
- [ ] Discriminated unions for states, with exhaustive `never` checks; no `enum`
- [ ] Clear names, small functions, no magic numbers, no dead or commented-out code

**React**
- [ ] No effect that could be a derivation, an event handler or a query; every effect cleans up
- [ ] Named `XProps`, destructured; no component defined inside another; keys from IDs
- [ ] No floating promises; `signal` passed through for cancellation
- [ ] Components under ~150 lines, split by responsibility

**UI**
- [ ] Every view state renders: loading, empty, error, success, offline, permission-limited as designed
- [ ] Strings from the catalogue; styles from tokens and shared primitives; no hex values or arbitrary pixel values
- [ ] Semantic elements; every control labelled; keyboard operable; visible focus; focus moves as the spec says
- [ ] Works at 360 px with no horizontal page scroll, and at 200% zoom

**Data**
- [ ] Every request goes through the shared HTTP client and is parsed with a schema
- [ ] Query keys from the feature's factory; invalidation matches the design
- [ ] Errors mapped through `toAppError`; optimistic updates roll back on error

**Security and privacy**
- [ ] No secrets in code or `VITE_*` variables; no tokens in browser storage
- [ ] No `dangerouslySetInnerHTML` without DOMPurify and an ADR; user URLs validated
- [ ] No PII in logs, analytics, error reports or URLs
- [ ] Any new external origin is in the CSP and the privacy review

**Tests**
- [ ] New logic has unit tests for the happy path, each error and the edge cases
- [ ] Components tested by role and label, with `userEvent`, for each state
- [ ] A new route has an E2E test and an axe scan
- [ ] A bug fix includes a test that failed before the fix

**Performance and observability**
- [ ] New routes are lazy; no heavy dependency on the first route; bundle budget holds
- [ ] Images have dimensions; skeletons at the final size
- [ ] The analytics events and error reports from the design are present and free of PII

## Giving feedback
- **Label each comment:** **blocker** (must fix), **suggestion** (optional), **question**, or **nit**.
- **Explain why,** and link the rule or pattern.
- **Approve once the blockers are fixed.** Don't hold a PR for nits.
