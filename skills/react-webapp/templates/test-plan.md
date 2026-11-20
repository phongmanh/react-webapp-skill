# Test plan: <App or feature>

| Version | Status | QA lead | Approvers |
|---|---|---|---|
| 0.1 | Draft | <name> | <product owner, tech lead> |

## 1. Scope
- **In scope:** <FR and NFR IDs>
- **Out of scope:** <…>
- **Regression scope** (for a feature): <…>

## 2. Levels and tools
| Level | Scope | Tools | Owner | When |
|---|---|---|---|---|
| Unit | Schemas, helpers, error mapping, hooks | Vitest, `renderHook` | Developers | Every PR |
| Integration | Feature components with real hooks; every state and validation rule | Vitest, Testing Library, MSW | Developers | Every PR |
| E2E + accessibility | Critical flows; axe per route and dialog | Playwright, `@axe-core/playwright` | Developers | Every PR (Chromium); nightly (full matrix) |
| System | End to end on staging, on the browser matrix | Playwright projects + manual | QA | Phase 5 |
| Acceptance | Must FRs | Staging | Product owner, pilot users | Phase 5 |

## 3. Browser and viewport matrix
| Browser | Version | Viewports | Why |
|---|---|---|---|
| Chrome | Latest | 360, 1440 px | Largest share |
| Safari (macOS) | Oldest supported | 1440 px | WebKit differences |
| Safari (iOS) | Oldest supported | 375 px, real device | Mobile WebKit, touch, virtual keyboard |
| Firefox | Latest | 1024 px | Gecko |
| Edge | Latest | 1440 px | Enterprise users |

## 4. NFR tests
| NFR ID | Test | Method / tool | Target | Result |
|---|---|---|---|---|
| NFR-PERF-01 | LCP on `/notes` | Lighthouse mobile preset on staging, median of 5 | | |
| NFR-SIZE-01 | Bundle size | `npm run build` output | | |
| NFR-A11Y-01 | Accessibility | axe per route and dialog; keyboard pass; screen-reader smoke | | |
| NFR-SEC-01 | Headers and CSP | Header scanner on staging | | |

## 5. Acceptance outline
| AT ID | FR | Scenario (Given / When / Then) | Result |
|---|---|---|---|

## 6. Environments and data
- MSW handlers (unit, integration, local dev)
- Staging backend and its URL
- Test accounts per role
- Synthetic test data (no production PII)

## 7. Entry and exit criteria
| Level | Entry | Exit |
|---|---|---|
| System | G4 approved; RC deployed to staging | All `ST-` tests run; no open S1/S2 defects |
| Acceptance | System exit criteria met | Product owner signs off |

## 8. Defect severity
| Severity | Meaning |
|---|---|
| S1 | Data loss, a security issue, or the app unusable |
| S2 | A Must FR is broken, with no workaround |
| S3 | A workaround exists |
| S4 | Cosmetic |

---

## Test summary report (Phase 5)
| Level | Planned | Run | Passed | Failed | Blocked |
|---|---|---|---|---|---|

- **NFR results vs targets:** <table or link; "Not verified: <reason>" where a check couldn't run>
- **Open defects:** S1 <n> · S2 <n> · S3 <n> · S4 <n> (accepted: <list>)
- **Residual risks:** <…>
- **Recommendation:** Go / Go with conditions / No-go, because <reason>
