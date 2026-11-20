# Phase 4: Implementation
**Gate:** G4 Code complete
**Deliverables:** code with unit tests, CI pipeline, release candidate (RC) build on a preview or staging deployment, RTM update
**Load:** [code-patterns](../reference/code-patterns.md), [architecture](../reference/architecture.md), [testing](../reference/testing.md), [review-checklist](../reference/review-checklist.md); for project setup, also [project-setup](../reference/project-setup.md), [design-style](../reference/design-style.md) and [security-privacy](../reference/security-privacy.md)

## Goal
Build the app exactly as designed, in small reviewed PRs, with tests and quality gates from the first commit.

## Entry criteria
- G3 approved; feature designs and contracts frozen.
- The repository, a CI runner, and a test backend or MSW handlers are available.

## Activities
### Step 0: project setup (new app only)
1. **Scaffold** with Vite's `react-ts` template next to the existing `docs/`, without overwriting anything ([project setup](../reference/project-setup.md#scaffold)). Pin the Node LTS line in `.nvmrc` and `engines`.
2. **Install the stack** from the architecture document, at the latest stable versions. Commit the lockfile. No dependency that the architecture doesn't list.
3. **Config:** strict `tsconfig` with `noUncheckedIndexedAccess`, the `@/` alias, Vitest with coverage thresholds, Playwright against the production build, the lint and format config ([config files](../reference/project-setup.md#config-files)).
4. **App foundations.**
   - Providers (`QueryClientProvider`), the router with a root error boundary and lazy routes.
   - The HTTP client with timeouts, typed errors and schema parsing.
   - Design tokens in `@theme` and the shared UI primitives ([design style](../reference/design-style.md)).
   - The app shell: skip link, landmarks, route focus and `document.title` handling.
   - Typed `import.meta.env`; no secrets in any `VITE_*` variable.
5. **Test infrastructure:** `src/test/setup.ts`, the MSW server with happy-path handlers from the contract, `renderWithProviders`.
6. **Process:** the CI pipeline below, branch protection on `main`, a PR template.
7. **Prove the pipeline.** Before writing features, merge one tiny vertical slice through it, e.g. a route that renders data from an MSW handler, with a unit test, an E2E test and an axe scan.

### Feature build order
Each step is one or more PRs, taken from the feature design's slice plan. Building the contract first means every later PR builds on a reviewed, tested shape.
1. **Schemas and logic:** Zod schemas and inferred types, pure helpers, and unit tests.
2. **Data:**
   - the API functions on the shared HTTP client;
   - the query-key factory, query and mutation hooks;
   - MSW handlers for success, each error and the edge cases, and hook tests.
3. **Components:**
   - presentational components that take props, with tests for each state;
   - the container component that wires hooks to them;
   - forms with their schema.
4. **Wiring:** the route entry (lazy), navigation item, feature flag, catalogue keys.
5. **Critical flow:** a Playwright test for the Must stories, plus an axe scan of each new route and dialog.

### Coding rules
- Follow the [code patterns](../reference/code-patterns.md) and the project's own rules. Where they conflict, the project's rules win.
- Branch names, commits and PRs reference the ticket and the FR IDs (e.g. Conventional Commits: `feat(orders): add list filters (FR-004)`).
- Keep the layers clean: no `fetch` in components, no server data copied into `useState`, no imports from another feature's internals.
- Hard-code nothing: no user-facing strings outside the catalogue, no hex colours or pixel values outside tokens, no URLs or secrets in code.
- Handle every error path in the design. Never swallow an error or a rejected promise.
- Add the analytics events and logs from the design. Never log PII or tokens.

### CI pipeline
Cheapest checks first. Any failure blocks the merge.
1. `npm ci`
2. `npm run typecheck` and `npm run lint`
3. `npm run format:check`
4. `npm run test:coverage`, with the coverage floor (e.g. ≥ 80% of lines in `src/features` and `src/lib`)
5. `npm run build`, then the bundle-size budget from the NFRs
6. `npm run test:e2e` against the production build, with axe scans
7. `npm audit --audit-level=high` and a secrets scan
8. On merge or nightly:
   - deploy a preview or staging build;
   - Lighthouse CI on the key routes, compared with the NFR budgets and the last `main` run. Fail or flag the build when a budget is broken or a result regresses beyond an agreed margin (e.g. 10%);
   - the full browser matrix in Playwright.

### Pull requests
- **Size and checks:**
  - ≤ ~400 changed lines (not counting the lockfile and generated files);
  - one concern;
  - CI green;
  - at least one approving review against the [review checklist](../reference/review-checklist.md).
- **Description:**
  - what changed and why, with the FR IDs;
  - for UI changes, screenshots at 360 px and 1440 px, and of each new state.
- **Deviations** from the approved design or contract need a CR, not just a PR comment.
- **The owner's code review mode** (STATUS.md):
  - *Approve before writing:* present each PR's files, every line, with a plain explanation of what each part does and why. Write the code only after approval, then run the checks.
  - *Review after writing:* open the PR, then walk the owner through it before merging.

### Definition of Done (per PR)
- Code follows the patterns.
- New logic has tests titled with their IDs; every async view has tests for each state.
- Strings are in the catalogue; styles use tokens.
- `npm run check` and CI are green, and the PR is reviewed.
- The RTM row is updated.

## Exit checklist (G4)
- [ ] All in-scope FRs implemented and merged; feature flags set for the release
- [ ] CI green on the release commit; coverage floor and bundle budget met
- [ ] No open high or critical findings from lint, `npm audit` or the secrets scan, unless formally accepted
- [ ] All code reviewed; no unapproved deviations from the designs
- [ ] RC built by CI from a tag and deployed to staging; source maps uploaded privately; smoke-tested
- [ ] Test environment, test accounts and test data ready; RTM updated

## Pitfalls
- **Building the UI first** against imagined data, then bending the contract to fit it.
- **Big-bang PRs** at the end of a feature.
- **Testing only the dev server.** The production build differs in code splitting, env variables and minification.
- **Suppressing lint rules** (`exhaustive-deps`, `no-floating-promises`) to make CI pass.
- **"Temporary" API keys** in a `VITE_*` variable, which ships them to every browser.
