# Phase 3: Detailed design
**Gate:** G3 Ready to build
**Deliverables:** one [feature design](../templates/feature-design.md) per feature (`design/<feature>.md`), integration and E2E test cases, RTM update
**Load:** [code-patterns](../reference/code-patterns.md), [ui-ux](../reference/ui-ux.md), [design-style](../reference/design-style.md), [testing](../reference/testing.md)

## Goal
Specify each feature precisely enough that any React developer can build it without guessing, and a reviewer can check the code against it.

## Entry criteria
- G2 approved; the architecture and ADRs are baselined.
- UI designs (e.g. Figma) exist for the features in scope, or there's a decision to use the [default design style](../reference/design-style.md) and its patterns.
- Backend contracts exist, at least as a draft OpenAPI spec.

## Activities
Fill in the template for each feature:
1. **Routes and screens.** List the routes with their design links, layout and auth. For each screen, define:
   - its [screen spec](../reference/ui-ux.md#screen-specs): purpose, primary action, layout per breakpoint, content order, focus rules, fixed copy;
   - its view state as a TypeScript discriminated union: loading, empty, error, success, plus permission-limited if it applies;
   - the user actions and their handlers;
   - its URL state (search params) and what survives a reload.
2. **Contracts and schemas.** The Zod schemas (or generated types) for every request and response, and the feature's public API (`index.ts`). Write them as TypeScript, not prose.
3. **Data.**
   - Endpoints: method, path, request, response, error codes.
   - The query-key factory, the query and mutation hooks, their `staleTime`, invalidation and any optimistic update.
   - What is stored in the browser, if anything, and its schema version.
   - The cache and refresh policy, following the architecture's data strategy.
4. **Forms.** Fields, the validation schema (shared with the API where possible), when errors show, the submit and pending behaviour, and server-error mapping to fields.
5. **Errors.** A table mapping each `AppError` to a catalogue key and a UI behaviour: retry, sign in again, an inline field error, or the route error boundary.
6. **Analytics.** Events and parameters from the tracking plan, with no PII.
7. **Accessibility and i18n.**
   - Landmarks, headings, labels, live-region announcements, focus after each transition.
   - New catalogue keys and plurals.
   - RTL and long-language concerns.
8. **Test cases.** Integration (`IT-`: components with real hooks and MSW) and E2E (`UI-`: Playwright flows plus an axe scan per route and dialog), each traced to an FR. Unit tests are written with the code in Phase 4.
9. **PR slice plan.** Split the work into small, reviewable PRs that follow the [build order](4-implementation.md#feature-build-order). Each PR has a one-line goal and stays at or below ~400 changed lines.
10. **Review.** Walk through each design with the tech lead and another frontend developer. QA reviews the test cases; the designer reviews the screen specs and states.

## Exit checklist (G3)
- [ ] Every in-scope FR is covered by a feature design
- [ ] Every screen has its spec and full view state, including empty, error, offline and permission-limited states
- [ ] Schemas, hook signatures and the feature's public API written in TypeScript
- [ ] Endpoints frozen; MSW handlers derivable from the contract
- [ ] Error-to-message table complete; new catalogue keys listed
- [ ] `IT-` and `UI-` test cases traced to FRs; RTM updated
- [ ] PR slice plan agreed; estimates fit the schedule
- [ ] Designs reviewed and approved; baseline tagged

## Pitfalls
- **Designing only the success state.** Most bugs live in loading, empty, error and offline.
- **Prose instead of types.** "The page loads the user" hides the error handling, caching and cancellation decisions.
- **Filters in component state** instead of the URL, so they're lost on reload and can't be shared.
- **One giant PR per feature,** which nobody can review well.
