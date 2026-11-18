# Phase 1: Requirements
**Gate:** G1 Requirements baseline
**Deliverables:** [requirements](../templates/requirements.md), acceptance outline (in the [test plan](../templates/test-plan.md)), [RTM](../templates/rtm.md), [STATUS](../templates/status.md)
**Load:** [ui-ux](../reference/ui-ux.md), [security-privacy](../reference/security-privacy.md) (for the ASVS level and the data inventory)

## Goal
Agree on what the app must do and how well, in terms a tester can verify. No design yet, except constraints the stakeholders impose.

## Entry criteria
- A sponsor and a product owner are named.
- The problem and the target users are known, at least roughly.

## Activities
1. **Brief.** Capture:
   - the problem;
   - goals with measurable KPIs (e.g. "70% of new users finish sign-up");
   - target users, their roles and main tasks;
   - what is in and out of scope;
   - constraints: deadline, budget, team, mandated backend, identity provider or design system;
   - approvers and top risks.
2. **Functional requirements.**
   - Write user stories, each with an ID (`FR-nnn`), a MoSCoW priority and Given/When/Then acceptance criteria in user-visible terms: what appears, what's announced, where focus goes.
   - Cover the unhappy paths: offline, slow network, server error, empty data, no permission for the action, session expired, a stale record edited by someone else, a reload or deep link into the middle of a flow.
3. **Non-functional requirements.** Each one gets a target, the condition it's measured under, and a verification method. These web NFRs are almost always needed:

   | Attribute | Example target (agree the real one) | Verified by |
   |---|---|---|
   | PERF loading | LCP p75 ≤ 2.5 s on a mid-range phone over "Fast 4G" | Lighthouse (mobile preset), real-user monitoring |
   | PERF responsiveness | INP p75 ≤ 200 ms; CLS p75 ≤ 0.1 | Lighthouse, real-user monitoring |
   | SIZE | Initial JS ≤ 200 kB gzip; each route chunk ≤ 100 kB gzip | `vite build` output in CI |
   | REL availability | Static host SLA; the app shell loads when the API is down and says so | System test |
   | REL offline | <what works offline: e.g. read-only cached data, or nothing> | System test |
   | COMPAT | Last 2 versions of Chrome, Edge, Firefox and Safari; iOS Safari 2 latest; widths from 360 px | Playwright projects, manual |
   | A11Y | WCAG 2.2 AA: 0 axe violations on every route and dialog; keyboard-only pass of core flows; 200% zoom | axe in Playwright, manual pass |
   | I18N | Listed locales; RTL yes/no; locale-aware dates, numbers, currency | Catalogue key test, pseudo-locale pass |
   | SEC | OWASP ASVS L1, or L2 for finance, health or identity data; security headers and CSP | ASVS checklist, header scan |
   | PRIV | Data minimisation; consent before non-essential cookies and analytics; account deletion | Privacy review |
   | MAINT | Typecheck, lint and format clean; coverage floor (e.g. ≥ 80% lines in features and lib) | CI |
   | OBS | Errors reported with release and route; no PII | Error-reporting dashboard |
4. **Platform scope.**
   - Supported browsers and versions, chosen from audience analytics if they exist;
   - devices and viewports (phone, tablet, laptop, large screen);
   - locales and countries;
   - rendering: SPA, or SEO-indexed public pages that need server rendering or prerendering;
   - whether installability (PWA), offline or push is in scope (usually not).
5. **Browser capabilities inventory.** For each browser permission or sensitive API (notifications, geolocation, camera, clipboard read, storage persistence): why it's needed, when it's requested, and what happens if it's denied. Prefer options that need no permission.
6. **Data inventory.** For each type of data collected: purpose, where it's stored (server, `localStorage`, IndexedDB, cookies), who it's shared with (including third-party scripts), and how long it's kept. This feeds the privacy policy, the cookie banner and the threat model.
7. **External interfaces.**
   - Backend APIs: owner, contract status, environments, CORS and auth model.
   - Identity provider, payment provider, analytics, error reporting, feature flags, CDNs and fonts.
   - Inbound links: URLs that must stay stable (emails, bookmarks, SEO).
8. **Acceptance outline.** Write one `AT-` scenario per Must story in the test plan.
9. **Validate.** Walk through the requirements with the product owner, a developer, QA, a designer and security. Each requirement must be clear, testable, necessary, and consistent with the others.
10. **Baseline.**
    - Create the RTM rows.
    - Resolve the open TBDs, or accept them explicitly.
    - Ask for sign-off.

## Exit checklist (G1)
- [ ] Every requirement has an ID, a priority and testable acceptance criteria
- [ ] Every NFR has a number, a condition and a verification method; no number is still marked "(proposed)"
- [ ] Data and browser-capability inventories complete; ASVS level chosen
- [ ] Browsers, viewports, locales and rendering needs agreed
- [ ] No open TBD blocks a Must requirement
- [ ] Acceptance outline covers every Must requirement; RTM created
- [ ] Approved by the product owner and the tech lead; baseline tagged

## Pitfalls
- **Unmeasurable NFRs** like "fast", "secure" or "responsive", which nobody can test.
- **Happy paths only.** Web apps fail most often on a slow network, after a reload mid-flow, and when the session expires.
- **Lab-only performance targets** measured on a developer laptop, when users are on mid-range phones.
- **Finding out at release time** that a third-party script sets cookies the consent banner doesn't cover.
- **Writing the design** (screens, libraries) into the requirements.
