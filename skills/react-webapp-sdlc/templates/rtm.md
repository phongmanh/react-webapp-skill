# Requirements traceability matrix: <App or feature>

Every requirement traces forward to design, code, tests and the release. Every test traces back to a requirement. Update this file in the same PR as the change.

Upstream source cites the backend or other inputs with a prefix (e.g. `BE-FR-002`); use "—" when the requirement is the app's own.

| Req ID | Summary | Priority | Upstream source | Design (architecture § / feature design) | Code (feature, PRs) | Tests (IDs) | Result | Release |
|---|---|---|---|---|---|---|---|---|
| FR-001 | View the notes list | M | BE-FR-002 | design/notes.md §1 | features/notes, #12 #14 | UT-003, IT-001, UI-001, AT-001 | Pass | v1.0.0 |
| NFR-PERF-01 | LCP p75 ≤ <n> s | M | — | architecture.md §1 | app (lazy routes, prefetch) | ST-010 | | |

## Coverage checks
| Check | Required |
|---|---|
| Requirements without a design | 0 at G3 |
| Must requirements without a passing test | 0 at G5 |
| Tests without a requirement | 0 (trace them, or remove them) |

Check the test side with `grep -rhoE "\b(FR-[0-9]+|NFR-[A-Z0-9]+-[0-9]+)\b" src e2e | sort -u`.
