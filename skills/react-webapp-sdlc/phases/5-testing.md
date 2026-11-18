# Phase 5: Testing
**Gate:** G5 Release readiness (go/no-go). Never skipped or combined.
**Deliverables:** test execution reports, defect log, UAT sign-off, test summary report (in the [test plan](../templates/test-plan.md)), RTM update
**Load:** [testing](../reference/testing.md), [security-privacy](../reference/security-privacy.md), [performance-reliability](../reference/performance-reliability.md), [ui-ux](../reference/ui-ux.md)

## Goal
Prove in real browsers that the app meets every requirement and NFR, and give the go/no-go decision a base of evidence.

## Entry criteria
- G4 approved; the RC is deployed to staging.
- The test plan is approved; environments, accounts and data are ready.

## Activities
1. **Run the test levels** from the master test plan. Unit and integration tests already pass in CI. System, NFR and acceptance tests use the **RC build** on staging (production config, minified, real hosting headers).

   | Level | What | Tools |
   |---|---|---|
   | Integration (`IT-`) | Feature components with real hooks and MSW: every state, every validation rule | Vitest, Testing Library, MSW |
   | E2E (`UI-`) | Critical flows; an axe scan of every route and dialog | Playwright, `@axe-core/playwright` |
   | System (`ST-`) | End to end against staging, on the browser and viewport matrix | Playwright projects, manual, a cloud browser grid if needed |
   | Acceptance (`AT-`) | The product owner and pilot users, on staging | The acceptance outline |
2. **NFR tests**, each against its requirement's target:
   - **Performance:**
     - Lighthouse (mobile preset) on the key routes of the staging build, several runs, median reported;
     - LCP, INP and CLS against their targets; the bundle sizes from the build output against the budget.
   - **Accessibility:**
     - axe on every route and dialog, in each meaningful state;
     - a keyboard-only walkthrough of the core flows;
     - a screen-reader smoke test (VoiceOver or NVDA) on sign-in and one core flow;
     - 200% zoom and 400% reflow at 320 px; `prefers-reduced-motion`.
   - **Security:**
     - the [ASVS checklist](../reference/security-privacy.md) at the agreed level;
     - security headers and CSP on the deployed build (e.g. a header scanner);
     - `npm audit` and the secrets scan clean;
     - try XSS payloads in every input and URL parameter, open-redirect parameters, and framing the app.
   - **Reliability:**
     - offline, a throttled network, an API that returns 500 or times out;
     - session expiry mid-flow; two tabs editing the same record;
     - reload and deep link into every route; browser Back and Forward through each flow.
   - **Upgrade:**
     - keep a tab open on the previous release, deploy the RC, then navigate: chunks load or the app recovers cleanly;
     - any browser-stored data from the previous version is migrated or discarded safely.
   - **Compatibility:** the browser matrix, including the oldest supported Safari, plus 360, 768, 1024 and 1440 px widths.
   - **i18n:** every supported language on every screen; the longest language at 360 px; RTL if in scope.
3. **Defects.**
   - Log each one with its steps, browser, viewport, build and severity:
     - S1: data loss, a security issue, or the app unusable;
     - S2: a Must FR is broken, with no workaround;
     - S3: a workaround exists;
     - S4: cosmetic.
   - Fix them in a new RC. Re-run the affected tests plus a regression subset, and add a regression test that carries the defect's ID.
4. **Test summary report.** Results per level, NFR results against their targets, open defects by severity, residual risks, and a recommendation. Only numbers from commands that actually ran; a check that couldn't run is marked **Not verified** with the reason.
5. **Go/no-go.** Present the report and the G5 checklist to the product owner, the tech lead and the QA lead.

## Exit checklist (G5)
- [ ] Every Must FR has a passing `AT-`, `UI-` or `ST-` test; the RTM shows full coverage
- [ ] Every NFR measured and within target, or the gap formally accepted
- [ ] No open S1 or S2 defects; S3 defects reviewed and accepted
- [ ] ASVS checklist passed at the agreed level; headers and CSP verified on staging
- [ ] Upgrade test (open tab across a deploy) passed
- [ ] UAT signed off; test summary report approved
- [ ] Release notes, privacy policy and cookie notice ready

## Pitfalls
- **Testing the dev server.** Differences in chunking, env variables, headers and caching only show up in the deployed build.
- **Only Chrome on a fast laptop.**
- **Scanning the loading spinner with axe** instead of the loaded state.
- **Lowering the exit criteria** to hit a date, instead of escalating the risk.
