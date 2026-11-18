# Phase 2: Architecture
**Gate:** G2 Architecture baseline
**Deliverables:** [architecture document](../templates/architecture.md) (threat model inside), [ADRs](../templates/adr.md), master [test plan](../templates/test-plan.md), RTM update
**Load:** [architecture](../reference/architecture.md), [security-privacy](../reference/security-privacy.md), [performance-reliability](../reference/performance-reliability.md), [testing](../reference/testing.md); [design-style](../reference/design-style.md) for the visual-design decision

## Goal
Decide how the app is structured to meet the requirements, especially the NFRs, and fix the stack. Every feature is then designed against the same rules.

## Entry criteria
- G1 approved; the requirements and RTM are baselined.
- The top 3–5 quality goals are ranked (e.g. accessibility > loading speed > offline).

## Activities
1. **Drivers.**
   - Turn the top NFRs into scenarios, e.g. "On a mid-range phone over Fast 4G, the orders list is usable within 2.5 s of opening the link."
   - Map each scenario to a tactic, e.g. route-level code splitting plus a cached query with a skeleton at the final size.
2. **Stack.**
   - Start from the [default stack](../reference/architecture.md#default-stack). Write an ADR only for a deviation or an open choice, e.g. SSR with a framework, TanStack Router, a mandated component library, or the error-reporting vendor.
   - Confirm the backend contract format; OpenAPI is preferred. Decide whether client types are generated from it or written as Zod schemas.
3. **Project layout.** Apply the [size rule](../reference/architecture.md#project-layout): one package with feature folders, or a workspace monorepo. Record the choice in an ADR and draw the dependency graph.
4. **Layer rules.**
   - Adopt the [layer rules](../reference/architecture.md#layers) and list any project-specific additions.
   - Enforce them in review, and with `import/no-cycle` plus restricted-import lint rules where possible.
5. **State and data strategy, per resource.** Decide and record:
   - where each kind of state lives ([state placement](../reference/architecture.md#state-placement));
   - the query keys, `staleTime` and what triggers a refetch;
   - optimistic updates, and where they're allowed;
   - what is persisted in the browser, if anything, and how it's versioned and cleared on sign-out;
   - the conflict policy for concurrent edits (e.g. `ETag` + `If-Match`, `412` shows a notice).

   See [reliability](../reference/performance-reliability.md#reliability).
6. **API integration.**
   - Base URLs per environment, through typed `VITE_*` variables (never secrets).
   - Auth: the session model (`HttpOnly` cookies from the backend or a BFF preferred), sign-in and refresh, CSRF protection.
   - The error model, pagination and API versioning.
   - How a new deployment reaches open tabs: chunk-load failures after a deploy, and an optional "new version available" notice.
7. **Routing.** The route tree with layouts, lazy routes, route-level error boundaries, auth guards (UX only; the server enforces), URL state for filters and paging, stable public URLs and redirects for old ones.
8. **Cross-cutting decisions.**
   - The `AppError` model and how it maps to user messages.
   - Forms: React Hook Form + Zod, or React 19 Actions (one approach per project).
   - Logging and error reporting without PII.
   - Feature flags and remote config.
   - i18n library and catalogue layout.
   - Visual design: the [default design style](../reference/design-style.md) and theme, or the brand's design system (ADR).
9. **Threat model.**
   - List the assets: sessions, PII, payments, admin actions.
   - List the entry points: forms, URL parameters, `postMessage`, uploads, rendered user content, third-party scripts, the API.
   - Apply STRIDE to each entry point (XSS, CSRF, clickjacking, open redirects, supply chain).
   - Map each mitigation to an ASVS control and a requirement ID. The CSP is part of the design.
10. **Observability.**
    - Error reporting with source maps uploaded privately, release and route tags.
    - Real-user Core Web Vitals.
    - The analytics tracking plan, with consent.
    - A release-health dashboard.
11. **Build and delivery.**
    - Environments: local, preview per PR, staging, production.
    - Hosting: SPA fallback, caching rules, security headers ([project setup](../reference/project-setup.md#hosting)).
    - CI stages, as in [Phase 4](4-implementation.md#ci-pipeline).
    - How a release is promoted and rolled back.
12. **Test strategy.** The master test plan covers:
    - test levels and tools;
    - the browser and viewport matrix;
    - test data and environments (MSW, staging, seeded accounts);
    - entry and exit criteria per level.
13. **Proofs of concept.** For each risky unknown, run a time-boxed, throwaway spike. Examples: the identity provider's redirect flow and cookie behaviour in Safari, the bundle cost of a charting library, a large table's scroll performance. Record the outcome in the ADR.
14. **Review.** Walk each driver scenario through the design with the tech lead, a senior frontend developer, a designer, QA and security.

## Exit checklist (G2)
- [ ] Each NFR maps to a tactic; driver scenarios walked through
- [ ] Stack deviations and project layout recorded in accepted ADRs
- [ ] State and data strategy defined for every resource: keys, freshness, persistence, conflicts
- [ ] Auth model, CSRF protection and CSP defined
- [ ] Threat model reviewed; mitigations mapped to ASVS controls and requirement IDs
- [ ] Observability, CI/CD, hosting and rollback defined
- [ ] Master test plan with the browser matrix approved
- [ ] Risky unknowns retired by a PoC or formally accepted
- [ ] RTM updated; baseline tagged

## Pitfalls
- **Adding libraries "because everyone uses them"** instead of because a requirement needs them. Each one is bundle weight and supply-chain risk.
- **Server state copied into a global store,** which then drifts from the server.
- **Tokens in `localStorage`** because it was easier than cookies, and an XSS bug then becomes an account takeover.
- **Forgetting open tabs,** which keep running the old bundle and fail to load chunks after a deploy.
- **Treating the threat model as paperwork.** Every mitigation must become a requirement or a design element.
