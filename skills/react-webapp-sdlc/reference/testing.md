# Testing reference

## Pyramid
| Level | Share (e.g.) | Runs on | Covers |
|---|---|---|---|
| Unit (`UT-`) | ~60% | Vitest (jsdom), on every PR | Schemas, formatters, reducers, error mapping, custom hooks (`renderHook`) |
| Integration (`IT-`) | ~30% | Vitest + Testing Library + MSW, on every PR | A feature's components with real hooks and mocked HTTP: every state, interactions, form validation |
| E2E (`UI-`) | ~10% | Playwright against the production build | Critical flows per acceptance criterion; an axe scan per route and dialog |
| System and NFR (`ST-`) | Per the test plan | Staging, browser matrix | End to end, Web Vitals, bundle budget, security headers, upgrade, compatibility |

## What to test in each layer
| Layer | Test | Test doubles |
|---|---|---|
| Schemas and lib | Every schema accepts valid and rejects invalid input; formatters per locale; `toAppError` for each status | None |
| Data hooks | Each query and mutation: success, each error, invalidation | MSW handlers |
| Components | Each view state renders; clicks and keyboard call the right callbacks; validation messages per rule | MSW, or a fixed view state for presentational components |
| Routes and flows | The user can complete each acceptance criterion; focus and title after navigation; no axe violations | `page.route` stubs or a seeded test backend |

## Conventions
- **Files.** Colocate tests: `NotesContent.tsx` next to `NotesContent.test.tsx`. E2E specs live in `e2e/<flow>.spec.ts`.
- **Titles start with the ID they verify:** `it('IT-003 FR-002 shows an error with Retry when loading fails', …)`, `test('UI-001 AT-001 creates a note', …)`. The RTM is checked by grepping these IDs.
- **Structure.** Arrange–Act–Assert, one behaviour per test, no logic (`if`, loops) in tests, no order dependence.
- **Test behaviour, not implementation.** Assert what the user sees and does, never internal state, hook calls or class names.
- **Query priority:** `getByRole` (with `name`) → `getByLabelText` → `getByText` → `getByTestId` as a last resort. If an element can't be found by role or label, that is often an accessibility bug.
- **Interaction** with `userEvent`, not `fireEvent`. Async with `findBy*` and `waitFor`. Never sleep; never `waitForTimeout`.
- **Deterministic.** No real network (`onUnhandledRequest: 'error'`); fake timers (`vi.useFakeTimers`) and a fixed `Date` where time matters; a fresh QueryClient per test with retries off.
- **Test data builders** with defaults keep tests short: `aNote({ title: 'x' })`.
- **Coverage.** Vitest enforces a floor (e.g. ≥ 80% lines, functions and statements, ≥ 75% branches over `src/features` and `src/lib`). The app shell and routes are covered by E2E. Coverage is a floor, not the goal.

## Snippets
Setup (`src/test/setup.ts`):
```ts
import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'
import { server } from './server'

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
})
afterAll(() => server.close())
```

MSW server (`src/test/server.ts`), with happy-path handlers written from the contract:
```ts
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

export const handlers = [
  http.get('/api/notes', () => HttpResponse.json({ items: [aNote({ title: 'Write the SRS' })], nextCursor: null })),
]
export const server = setupServer(...handlers)
```
Override per test with `server.use(...)` for error, empty and edge cases. A request the contract doesn't cover fails the test: that's a contract gap to fix in the design or the code, through a CR if it changes the contract.

Render helper (`src/test/render.tsx`):
```tsx
export function renderWithProviders(ui: ReactElement, { route = '/' }: { route?: string } = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
    </QueryClientProvider>,
  )
}
```

Integration test:
```tsx
describe('NotesPage', () => {
  it('IT-003 FR-001 shows an error with Retry, then the notes after a retry', async () => {
    server.use(http.get('/api/notes', () => new HttpResponse(null, { status: 500 }), { once: true }))
    renderWithProviders(<NotesPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Something went wrong. Try again.')
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))

    expect(await screen.findByRole('link', { name: 'Write the SRS' })).toBeInTheDocument()
  })

  it('IT-004 FR-001 shows the empty state with a create action', async () => {
    server.use(http.get('/api/notes', () => HttpResponse.json({ items: [], nextCursor: null })))
    renderWithProviders(<NotesPage />)

    expect(await screen.findByRole('heading', { name: 'No notes yet' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Create note' })).toHaveAttribute('href', '/notes/new')
  })
})
```

Hook test:
```tsx
it('UT-007 FR-002 creating a note invalidates the list', async () => {
  const { result } = renderHook(() => useCreateNote(), { wrapper })
  result.current.mutate({ title: 'Design', body: '' })
  await waitFor(() => expect(result.current.isSuccess).toBe(true))
})
```

E2E and accessibility (`e2e/notes.spec.ts`):
```ts
import { AxeBuilder } from '@axe-core/playwright'
import { expect, test } from '@playwright/test'

test.beforeEach(async ({ page }) => {
  await page.route('**/api/notes*', (route) =>
    route.fulfill({ json: { items: [{ id: '1', title: 'Write the SRS', body: '', updatedAt: '2026-01-01T00:00:00Z' }], nextCursor: null } }),
  )
})

test('UI-001 AT-001 lists notes and opens one', async ({ page }) => {
  await page.goto('/notes')
  await expect(page.getByRole('heading', { level: 1, name: 'Notes' })).toBeFocused()
  await page.getByRole('link', { name: 'Write the SRS' }).click()
  await expect(page).toHaveURL(/\/notes\/1$/)
})

test('ST-020 NFR-A11Y-01 notes list has no WCAG 2.2 AA violations', async ({ page }) => {
  await page.goto('/notes')
  await expect(page.getByText('Write the SRS')).toBeVisible() // scan the loaded state, not the spinner
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
    .analyze()
  expect(results.violations).toEqual([])
})
```
- Import `{ AxeBuilder }` as a named import; the default import fails to typecheck under `nodenext`.
- Web-first assertions (`await expect(locator).toBeVisible()`) with role-based locators.
- Scan every route in each meaningful state (e.g. with a dialog open, with a form error shown).
- Add Playwright `projects` for each browser and viewport the compatibility NFR requires.

## NFR verification
| NFR type | How to verify | Evidence |
|---|---|---|
| Performance (LCP, INP, CLS) | Lighthouse (mobile preset) on the staging build, 3–5 runs, median; real-user p75 after release | Metric values per route |
| Bundle size | `npm run build` output (gzip sizes per chunk) | The table from the build output |
| Accessibility | axe in E2E, the keyboard pass, a screen-reader smoke test, zoom and reflow | Pass/fail per route and flow |
| Compatibility | Playwright projects for each browser and viewport; a manual pass on real iOS Safari | Run summary |
| Security | `npm audit --audit-level=high`, a secrets scan, a header and CSP check on staging, XSS and redirect probes | Command output, scanner report |
| Reliability | Offline, throttled network, 500 and timeout responses, session expiry, two-tab edits, reload and deep link per route | Pass/fail per scenario |
| Upgrade | A tab open on the previous release across a deploy | Pass/fail |

Report actual numbers only. If a check couldn't be run, mark it **Not verified**, give the reason, and leave the decision to the gate.

## Tracing tests to requirements
```bash
grep -rhoE "\b(UT|IT|UI|ST|AT)-[0-9]+\b" src e2e | sort -u   # test IDs that exist
grep -rhoE "\b(FR-[0-9]+|NFR-[A-Z0-9]+-[0-9]+)\b" src e2e | sort -u   # requirements that have tests
```
Any Must requirement in `rtm.md` missing from the second list has no test.

## Commands
| Purpose | Command |
|---|---|
| Typecheck + lint + format check + unit and integration tests (the per-PR gate) | `npm run check` |
| Unit and integration tests in watch mode | `npm test` |
| Coverage report and floor | `npm run test:coverage` |
| E2E and axe against the production build | `npm run test:e2e` |
| One E2E spec, headed, for debugging | `npx playwright test e2e/notes.spec.ts --headed` |
| Production build and bundle sizes | `npm run build` |
| Dependency advisories | `npm audit --audit-level=high` |
