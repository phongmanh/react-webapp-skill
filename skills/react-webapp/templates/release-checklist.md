# Release checklist: <App> v<semver>

| Release owner | Target date | Rollout plan | G5 decision |
|---|---|---|---|
| <name> | YYYY-MM-DD | Atomic deploy + instant rollback / flag ramp | <date, approver> |

## Build
- [ ] Built by CI from the tag `v<semver>`; the artifact that passed G5 is the one promoted
- [ ] Production env variables set in CI; no secrets in any `VITE_*` variable
- [ ] Release version and commit embedded and reported with errors
- [ ] Source maps uploaded to the error reporter; not served publicly
- [ ] Bundle within the size budget

## Hosting
- [ ] SPA fallback to `index.html`
- [ ] `index.html` served `no-cache`; `/assets/*` immutable
- [ ] Security headers and CSP as designed, verified on the production URL
- [ ] HTTPS with HSTS; domain, DNS and certificates ready
- [ ] Redirects for changed public URLs; robots and sitemap if public pages are in scope

## Privacy and legal
- [ ] Privacy policy and cookie notice match the data inventory, including third-party scripts
- [ ] Consent gates non-essential cookies and analytics
- [ ] Account deletion (and data export, if required) works

## Readiness
- [ ] G5 go decision recorded; test summary report approved
- [ ] Backend changes deployed first and compatible with the previous frontend
- [ ] Feature flags set; kill switches tested on staging
- [ ] Rollback tested; the previous deployment is one step away
- [ ] Dashboards and alerts live; on-call owner named
- [ ] Support team briefed; known issues documented

## Rollout
| Step | Exposure | Earliest date | Halt if… | Decision |
|---|---|---|---|---|
| 1 | Production deploy, flag off; smoke test | | Any S1 defect | |
| 2 | Flag on for internal users | | Error rate > <n>% | |
| 3 | Flag 5% → 25% → 100% (≥ 1 day per step for risky features) | | Error rate > <n>%, LCP p75 > <n> s, KPI drop > <n>% | |

On a halt:
1. Switch off the feature flag, or roll back to the previous deployment.
2. Tell support what's affected.
3. Fix forward through the hotfix path.

## Hypercare (<n> days)
- [ ] Daily check of errors, Web Vitals, KPIs and support tickets; findings logged

## Handover and sign-off
- [ ] Runbook, dashboards, open defects and known limitations handed over to <maintenance owner>
- [ ] RTM closed; lessons learned recorded

| Role | Name | Decision | Date |
|---|---|---|---|
