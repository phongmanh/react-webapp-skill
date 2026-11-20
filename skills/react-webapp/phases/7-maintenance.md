# Phase 7: Maintenance
**Gate:** each change runs a small gated cycle: CR → design delta (G3-lite) → G5 → release
**Deliverables:** health reviews, [change requests](../templates/change-request.md), hotfix releases, [postmortems](../templates/postmortem.md) for S1 incidents, updated RTM and docs
**Load:** [review-checklist](../reference/review-checklist.md), [performance-reliability](../reference/performance-reliability.md), plus the phase files the change's size calls for

## Goal
Keep the app fast, secure, accessible and compliant as browsers, dependencies, the backend and the law change. Evolve it without breaking what works.

## Activities
1. **Monitor.**
   - Weekly: client error rate and top errors by release and browser, real-user Web Vitals (p75 by route and device class), KPIs, support tickets.
   - Each release: compare against the previous release.
2. **Triage** by severity, with a response time for each:
   - S1 (error spike, data loss, security issue): run the incident path below now.
   - S2: next release.
   - S3 and S4: backlog.
3. **Incident and hotfix path** (S1).
   1. **Contain:** roll back to the previous deployment, or switch off the feature's kill switch.
   2. **Communicate:** tell product and support what is affected and when to expect a fix. Update them until it's resolved.
   3. Branch from the release tag.
   4. Make a minimal fix, with a test that failed before the fix.
   5. Expedited review.
   6. G5-lite: the fix plus a regression subset, on staging.
   7. Release with a new patch version.
   8. Merge back to `main`.
   9. Within a week, write a blameless [postmortem](../templates/postmortem.md): fix the system, not the person. Its action items get owners and dates, and become CRs or tickets.
4. **Change requests.** Every new feature, or change to baselined behaviour, starts with a CR: impact via the RTM, then a decision.
   - A small change runs design delta → implement → test → release.
   - A big one runs the full lifecycle in a new workspace.
5. **Platform updates.**
   - Node: move to the next LTS line before the current one reaches end of life; update `.nvmrc`, `engines` and CI together.
   - Browsers: review the supported-browser list against analytics twice a year.
   - Framework majors (React, the router, the build tool, the test runner): one CR each, following the official migration guide, with the full test suite and an NFR re-check.
6. **Dependencies.**
   - Automated update PRs every week or month (e.g. Renovate or Dependabot), grouped by risk.
   - Security advisories immediately.
   - Remove dependencies that are no longer used; watch the bundle budget.
7. **Tech debt.** Keep a ranked debt list, and reserve a fixed share of each release for it (e.g. 15–20%).
8. **Documentation.** When the code changes, update the architecture document, ADRs and feature designs in the same PR.
9. **End of life.** Retire a feature or a route with notice:
   1. switch the flag off;
   2. redirect its URLs;
   3. remove the code, catalogue keys and tests;
   4. clean up the backend and any stored browser data.

## Checklist per release
- [ ] Every change in scope has an approved CR; RTM updated
- [ ] Regression suite and affected NFR tests passed
- [ ] Node, framework and dependencies within policy; no open high or critical advisories
- [ ] Release checklist completed; rollout with halt criteria
- [ ] Every S1 since the last release has a postmortem, and its action items are tracked

## Pitfalls
- **Hotfixes that skip tests** and cause the next incident.
- **Postmortems that blame a person,** or action items with no owner or date, so the same incident happens again.
- **Running an end-of-life Node or framework version,** which stops getting security fixes.
- **Letting dependencies age** until one update becomes a migration project.
- **Docs that stop matching the code** after the first year.
