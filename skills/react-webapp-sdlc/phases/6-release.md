# Phase 6: Release
**Gate:** G6 Launch accepted
**Deliverables:** completed [release checklist](../templates/release-checklist.md), rollout record, handover pack
**Load:** [project-setup](../reference/project-setup.md#hosting), [performance-reliability](../reference/performance-reliability.md#observability), [security-privacy](../reference/security-privacy.md#privacy)

## Goal
Ship the approved build to production safely, watch it, and hand it over to the team that runs it.

## Entry criteria
- G5 approved, with the go decision recorded.
- Access to the hosting, DNS and monitoring accounts is in place; the release owner and the on-call owner are named.

## Activities
1. **Build.**
   - CI builds the production bundle from the tagged commit (`v<semver>`), with the production env variables. The same artifact that passed G5 is promoted; nothing is rebuilt by hand.
   - The version and commit are embedded in the bundle and reported with every error.
   - Source maps are uploaded to the error reporter and not served publicly (or served only behind auth).
2. **Hosting.**
   - SPA fallback to `index.html`; `index.html` served with `Cache-Control: no-cache`; hashed `/assets/*` immutable.
   - Security headers and CSP as designed; HTTPS with HSTS.
   - Custom domain, DNS and certificates; redirects for any changed public URLs.
   - Robots, sitemap and meta tags if public pages are in scope.
3. **Privacy and legal.**
   - The privacy policy and cookie notice match the data inventory, including third-party scripts.
   - Consent gates non-essential cookies and analytics.
   - Account deletion works if the app has accounts.
4. **Rollout.** Choose one in the architecture, and record it:
   - **Atomic deploy with instant rollback** (most static hosts): deploy, smoke-test, keep the previous deployment one click away.
   - **Gradual exposure:** a percentage rollout at the edge, or a feature flag ramp, e.g. internal → 5% → 25% → 100%, with at least a day per step for risky features.
5. **Halt criteria**, agreed before the rollout starts. For example:
   - the client error rate goes above its target;
   - a Core Web Vitals p75 breaks its budget;
   - a new S1 defect appears;
   - a key KPI drops by more than an agreed percentage.

   On a halt:
   1. Switch off the feature flag, or roll back to the previous deployment.
   2. Tell support what's affected.
   3. Fix forward through the hotfix path ([Phase 7](7-maintenance.md)).
6. **Safety nets.**
   - Remote config for the feature flags and kill switches. Each flag has a safe default for when config can't load, an owner and a removal date. Remove flags after launch: they are tech debt.
   - Test each kill switch on staging before the rollout starts.
   - Chunk-load failures after a deploy trigger one reload (or a "new version available" notice), never a blank screen.
   - Backend changes deploy first and stay compatible with the previous frontend.
7. **Hypercare** (e.g. 1–2 weeks).
   - Review the error reporter, real-user Web Vitals, KPIs and support tickets every day.
   - Name the on-call owner.
8. **Handover** to the maintenance team:
   - a runbook covering build, deploy, rollback, disabling a feature through flags, and hotfixes;
   - dashboards and alert owners;
   - open defects and known limitations.
9. **Close.**
   - Finish the RTM (requirement → release).
   - Record lessons learned.
   - Archive the baselines.

## Exit checklist (G6)
- [ ] Rollout complete with no halt criteria hit, or every halt resolved
- [ ] Error rate, Web Vitals and KPIs within target during hypercare
- [ ] Source maps uploaded privately; dashboards and alerts live
- [ ] Rollback tested and documented
- [ ] Handover accepted by the maintenance owner
- [ ] RTM closed; lessons learned recorded

## Pitfalls
- **Caching `index.html` for a long time,** so users keep loading a bundle that no longer exists.
- **Inventing halt criteria** after things have gone wrong.
- **Public source maps** that hand out the full source and comments.
- **A cookie notice that doesn't match** what a third-party script actually sets.
- **No kill switch** for a risky feature.
