# Architecture reference

A feature-based React app with one-way data flow: server state in TanStack Query, URL state in the router, form state in React Hook Form, and components that render state and forward events. The canonical code for each piece is in [code-patterns.md](code-patterns.md); scaffolding and config are in [project-setup.md](project-setup.md).

## Layers
```
routes (lazy pages, error boundaries) ──▶ features/<name> (components, hooks, api, schemas) ──▶ components/ui, lib (http, cn, formatters)
```
- **Schemas are the contract.** Each feature's Zod schemas define its data, and the TypeScript types are inferred from them. Every value from outside the app (HTTP, storage, URL params, `postMessage`) is `unknown` until a schema has parsed it.
- **Only the API layer talks HTTP.** A feature's `api/` module calls the shared client in `lib/http.ts` and exposes query and mutation hooks. Components never call `fetch`.
- **Components depend on hooks, not on transport.**
  - A container component calls hooks and passes data and intent callbacks down.
  - Presentational components take props and render. They hold no data fetching and no business rules.
- **Data flows one way.** State goes down as props; events come up as `onX` callbacks. Each async view renders one discriminated state: loading, empty, error or success.
- **Dependencies point downward.** `routes → features → components/ui, lib`. Lower layers never import upward, and features import each other only through their `index.ts`.

## Project layout
Choose one layout in a Phase 2 ADR.

**A. One package with feature folders**, for most apps:
```
src/
  app/                 # providers, router, root layout, app shell
  routes/              # route-level pages (lazy-loaded), RouteError
  features/
    <feature>/
      api/             # API functions, query-key factory, query and mutation hooks
      components/      # feature components (+ colocated *.test.tsx)
      hooks/           # feature logic hooks
      schemas.ts       # Zod schemas + inferred types
      index.ts         # the feature's public API
  components/ui/       # shared presentational primitives (Button, Field, Dialog)
  lib/                 # framework-agnostic helpers: http client, cn(), formatters, i18n
  test/                # setup.ts, MSW server and handlers, renderWithProviders
  main.tsx
e2e/                   # Playwright specs
```

**B. Workspace monorepo**, for growing products:
```
apps/web/              # the app: app/, routes/, features/ as in layout A
packages/ui/           # the design system: tokens and primitives
packages/api-client/   # generated or hand-written schemas and client for the backend
packages/config/       # shared tsconfig, lint and test config
```
In layout B, apps depend on packages, packages never depend on apps, and features still never import another feature's internals.

**Size rule.** Choose B if any of these hold; otherwise choose A:
- two or more apps share UI or API code (e.g. a customer app and an admin app);
- more than ~5 developers, or 2+ teams;
- the design system is published for other products;
- builds or tests already hurt in one package.

In either layout, **organise by feature** (`features/orders/`, `features/settings/`). That keeps a later move from A to B mechanical.

## Default stack
Always use the latest stable versions, recorded in `package.json` with a committed lockfile. A deviation needs an ADR.

| Concern | Default | Notes |
|---|---|---|
| Runtime | Node LTS, pinned in `.nvmrc` and `engines` | An odd (non-LTS) Node can make npm install older majors |
| Build and dev | Vite + `@vitejs/plugin-react` | Static output that deploys to any host |
| UI | React 19 | `ref` as a prop, Actions, `use` |
| Language | TypeScript, strict, with `noUncheckedIndexedAccess` | The version the Vite template pins |
| Routing | React Router, data mode (`createBrowserRouter`) | Route-level `lazy` and `ErrorBoundary` |
| Server state | TanStack Query | Caching, retries, invalidation, cancellation |
| Validation | Zod | One schema gives runtime validation and the TS type |
| Forms | React Hook Form + `@hookform/resolvers` (Zod) | Or React 19 Actions for simple forms; one approach per project |
| Styling | Tailwind CSS v4 (`@tailwindcss/vite`) + `clsx` + `tailwind-merge` | Tokens in `@theme`; see [design-style.md](design-style.md) |
| UI primitives | Native elements (`<dialog>`, `<button>`) | Radix or React Aria via ADR when the design needs menus, comboboxes and the like |
| Error boundaries | React Router `ErrorBoundary` per route; `react-error-boundary` for widgets | |
| Shared client state | Context for rarely changing values | Zustand via ADR for frequent updates |
| i18n | A message catalogue per locale, with `Intl` for formats | Library chosen in an ADR when there's more than one language |
| Lint | oxlint with type-aware rules and the react, jsx-a11y, import and vitest plugins | ESLint + typescript-eslint `strictTypeChecked` if that's the team standard |
| Format | Prettier + `prettier-plugin-tailwindcss` | |
| Unit and integration tests | Vitest + jsdom + Testing Library (react, user-event, jest-dom) | See [testing.md](testing.md) |
| API mocking | MSW | One set of handlers for tests and, optionally, dev |
| E2E and accessibility | Playwright + `@axe-core/playwright` | Against the production build |
| Error reporting and RUM | Chosen in an ADR (e.g. Sentry) | Source maps uploaded privately by CI |

Optional, each needs an ADR: the React Compiler (then stop hand-writing `useMemo`/`useCallback`), shadcn/ui, TanStack Virtual for long lists, a PWA service worker.

## When to deviate
| Requirement | Instead of the default |
|---|---|
| SEO-critical public pages, SSR or SSG, or a server must hold secrets (BFF) | Next.js App Router, or React Router framework mode |
| Type-safe routes and search params are central | TanStack Router |
| The organisation mandates a design system or component library | Use it instead of Tailwind and the default primitives |
| No backend exists yet | Keep the SPA and run the MSW handlers as the dev backend; the contract in the feature designs is the spec the backend must meet |
| An OpenAPI contract is stable and large | Generate the client and schemas from it (e.g. into `packages/api-client`) instead of writing them by hand |

## State placement
| Kind | Example | Where it lives |
|---|---|---|
| Server state | lists and records from the API | TanStack Query, never copied into `useState` |
| URL state | filters, sort, page, selected tab, open detail | Router search params or path, so it's shareable and survives reload |
| Form state | field values, validation errors | React Hook Form |
| Local UI state | open or closed, hover, wizard step | `useState` / `useReducer` in the lowest common owner |
| Shared client state | theme, current session summary | Context (rarely changing) or Zustand (frequent updates) |
| Persisted browser state | drafts, preferences | `localStorage` or IndexedDB behind a hook, parsed with a schema, versioned, cleared on sign-out |

Keep a single source of truth, lift state only as high as needed, and derive everything else during render.

## Error model
- `lib/http.ts` throws a typed `HttpError` (status, code, request ID) for non-2xx responses, and a `ZodError` when a response breaks the contract. A timeout or network failure surfaces as a `NetworkError`.
- `lib/errors.ts` maps every error to an `AppError` (`network`, `unauthorized`, `forbidden`, `notFound`, `conflict`, `validation`, `rateLimited`, `server`, `unknown`) in one function.
- Presentation maps an `AppError` to a catalogue key in one function. It shows the result in the view's error state, inline on the field for `validation`, or in the route's error boundary for a crash.
- Contract violations (`ZodError`) are bugs: report them, and surface them loudly in development.
- Never swallow an error. `AbortError` from a cancelled request is the one error that is ignored on purpose.

## Async and side effects
- Effects only synchronise with systems outside React (subscriptions, browser APIs, non-React widgets). Derive values during render, respond to events in handlers, fetch with TanStack Query.
- Every effect that subscribes, listens or starts a timer returns a cleanup.
- Pass the `signal` from TanStack Query through to `fetch`, so leaving a screen cancels its requests.
- No floating promises: every promise is awaited, returned, or handled with `void` plus an explicit `.catch`. The type-aware lint rule enforces it.
