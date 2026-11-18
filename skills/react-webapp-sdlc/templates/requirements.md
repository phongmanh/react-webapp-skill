# Requirements: <App or feature>

| Version | Status | Owner | Approvers |
|---|---|---|---|
| 0.1 | Draft | <product owner> | <product owner, tech lead> |

## 1. Brief
- **Problem:** <who has which problem today>
- **Goals and KPIs:** <measurable, e.g. "70% of new users finish sign-up">
- **Target users:** <roles, main tasks, devices and browsers they use, accessibility needs>
- **In scope:** <…>
- **Out of scope:** <…>
- **Constraints:** <deadline, budget, team, mandated backend, identity provider or design system, compliance>
- **Top risks:** <see the STATUS risk register>

## 2. Functional requirements
| ID | User story | Priority (M/S/C/W) | Acceptance criteria (Given / When / Then) |
|---|---|---|---|
| FR-001 | As a <user>, I want <goal>, so that <value> | M | Given … when … then …<br>Error: …<br>Empty: …<br>Session expired: … |

## 3. Non-functional requirements
| ID | Requirement | Target and condition | Verified by |
|---|---|---|---|
| NFR-PERF-01 | Loading | LCP p75 ≤ <n> s on <device profile, network> | Lighthouse, RUM |
| NFR-PERF-02 | Responsiveness and stability | INP p75 ≤ <n> ms; CLS p75 ≤ <n> | Lighthouse, RUM |
| NFR-SIZE-01 | Bundle size | Initial JS ≤ <n> kB gzip; route chunk ≤ <n> kB gzip | Build output in CI |
| NFR-REL-01 | Resilience | <what works when the API is slow, failing or offline> | System test |
| NFR-COMPAT-01 | Browsers and viewports | <browsers and versions>; widths from <n> px | Playwright projects, manual |
| NFR-A11Y-01 | Accessibility | WCAG 2.2 AA: 0 axe violations per route; keyboard-only core flows; 200% zoom | axe, manual pass |
| NFR-I18N-01 | Languages | <locales>; default <locale>; RTL <yes/no> | Catalogue key test, manual |
| NFR-SEC-01 | Security level | ASVS <L1/L2>; CSP and security headers | ASVS checklist, header scan |
| NFR-PRIV-01 | Privacy | <consent, retention, account deletion, data export> | Privacy review |
| NFR-MAINT-01 | Maintainability | Typecheck, lint and format clean; coverage ≥ <n>% lines in features and lib | CI |
| NFR-OBS-01 | Observability | Errors reported with release and route; no PII | Error-reporting dashboard |

## 4. Platform and browsers
| Item | Value |
|---|---|
| Browsers | <e.g. last 2 Chrome, Edge, Firefox, Safari; iOS Safari 2 latest> (audience data: <source>) |
| Viewports | Phone (from 360 px) · Tablet · Laptop · Large screen |
| Reference device profile | <e.g. Lighthouse mobile preset, or a named mid-range phone> |
| Rendering | SPA / public pages indexed by search engines (SSR or prerendering) |
| Installable / offline / push | In or out of scope |
| Distribution | <domains, countries, intranet or public> |

## 5. Browser capabilities inventory
| Capability | Why (FR) | When requested | If denied | Alternatives considered |
|---|---|---|---|---|
| e.g. Notifications | FR-010 reminders | When the first reminder is set | Reminders by email only; a note in settings | — |

## 6. Data inventory
This section feeds the privacy policy, the cookie notice and the threat model.

| Data type | Purpose | Stored (server / cookie / browser storage) | Encrypted | Shared with (including third-party scripts) | Retention |
|---|---|---|---|---|---|

## 7. External interfaces
| Interface | Owner | Contract (link, status) | Environments | Notes |
|---|---|---|---|---|
| Backend REST API | | OpenAPI <link> | dev / staging / prod | Auth model, CORS |
| Identity provider | | | | |
| Third-party scripts (analytics, error reporting, payments, fonts) | | | | |
| Stable inbound URLs (emails, bookmarks, SEO) | | | | |

## 8. Acceptance outline
One `AT-` scenario per Must FR, kept in [test-plan.md](test-plan.md) §5.

## 9. Assumptions and open items
- ASSUMPTION: <…>
- TBD-1: <…>

## 10. Sign-off
| Role | Name | Decision | Date |
|---|---|---|---|
