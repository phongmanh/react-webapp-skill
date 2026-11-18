# Performance, reliability & observability reference

Measure on a mid-range phone profile (e.g. Lighthouse's mobile preset: a slow CPU and a throttled network) against the production build. Never judge performance on the dev server: it's unbundled and unminified. The budgets come from the NFRs.

## Performance
### Core Web Vitals
Defaults unless the NFRs say otherwise, at the 75th percentile of real users: **LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1**.
- **LCP (loading).**
  - Keep the initial bundle small: route-level code splitting with `lazy`, and no heavy library on the first route.
  - Start data requests early: prefetch the first route's query in the route `loader`, or with `queryClient.prefetchQuery` on link hover or focus.
  - The LCP image gets `fetchpriority="high"`, explicit `width`/`height`, and isn't lazy-loaded.
  - Self-host fonts with `font-display: swap` and only the subsets and weights the copy needs.
- **INP (responsiveness).**
  - Keep event handlers short; move heavy work out of the click (a Web Worker, or `startTransition` for non-urgent updates).
  - Avoid re-rendering large trees on every keystroke: keep state local, use uncontrolled inputs (React Hook Form), and `useDeferredValue` for expensive filtering.
  - Virtualise long lists (more than ~100 rows) with TanStack Virtual.
- **CLS (stability).**
  - Skeletons and images at their final size; reserve space for banners and notices.
  - No content inserted above what the user is reading, except in response to their action.

### Bundle
- Check `vite build` output against the budget in CI; fail the build when a chunk grows past it.
- Prefer platform APIs (`Intl`, `URL`, `structuredClone`, `fetch`, `<dialog>`) over libraries; import narrowly (`import { format } from 'date-fns'`, not the whole package).
- Look at a bundle visualiser before adding a dependency and before each release.

### Rendering
- **Measure before optimising** with the React DevTools Profiler and a Performance trace.
- If the React Compiler is on, don't hand-write `useMemo`/`useCallback`/`memo`. If it's off, memoise only where a measurement shows a problem, or where referential stability is required (a value in another hook's dependency array).
- **When a screen is slow:**
  1. Reproduce it on the production build with CPU throttling.
  2. Record a Performance trace; look at long tasks, layout thrashing and forced reflows.
  3. Use the Profiler to find components that re-render without their props changing, and why.
  4. Fix the cause, then compare Lighthouse or a scripted interaction timing before and after.

### Network and caching
- Hashed `/assets/*` are `immutable` for a year; `index.html` is `no-cache`, so a deploy reaches users on their next load.
- TanStack Query `staleTime` per resource, from the data strategy; deduplicates identical requests.
- Paginate server-side (cursor paging) for lists that can grow.
- Compress with Brotli or gzip at the host; HTTP/2 or HTTP/3.

## Reliability
- **Every async view** has loading, empty, error and success states, and the error state offers Retry.
- **Retries.**
  - TanStack Query retries network errors and 5xx a small number of times with backoff; never 4xx.
  - Honour `429` and `503` with `Retry-After`.
  - Never blindly retry a request that isn't idempotent; send an **idempotency key** with creates that may be retried.
- **Concurrency.** Edits send `If-Match` with the record's `ETag`; a `412` shows a notice and keeps the user's input.
- **Offline,** where the requirements need it:
  - show cached data with an offline notice (`navigator.onLine` plus the `online`/`offline` events, confirmed by request failures);
  - queue writes only if the requirements ask for it, with an idempotency key and a visible pending state;
  - a service worker only with an ADR (it's a second deployment to keep consistent).
- **Deploys and open tabs.**
  - A lazy route whose chunk no longer exists fails to import. The route error boundary detects it and reloads once.
  - Optionally poll a `version.json` and show "A new version is available" with a Reload button.
  - The backend stays compatible with the previous frontend for at least one release.
- **Tolerant parsing.** Unknown fields are ignored; enums the backend may extend fall back to an "other" value; optional fields have defaults.
- **Browser storage** is versioned: a value with an old or unknown version is migrated or discarded, never trusted blindly.
- **Error boundaries** per route and around risky widgets, so one failure doesn't blank the app.
- **Safety nets:** a remote-config kill switch for each risky feature, and instant rollback at the host.

## Scalability (client side)
- **Organise by feature** along the [project layout](architecture.md#project-layout), so features and teams scale independently.
- **Protect the backend.**
  - Deduplicate and cache requests (TanStack Query).
  - Debounce search-as-you-type (e.g. 300 ms) and cancel superseded requests.
  - Paginate everywhere.
  - Poll only while the tab is visible (`refetchIntervalInBackground: false`), with jitter, and prefer server push (SSE or WebSocket) where the backend offers it.
- **Feature flags** separate deploying from releasing, and let you shed load in an incident.

## Observability
- **Error reporting** (e.g. Sentry) with:
  - the release version and commit, the route, the browser;
  - source maps uploaded by CI and not served publicly;
  - unhandled rejections and error-boundary catches reported;
  - PII scrubbed from URLs, breadcrumbs and payloads.
- **Real-user monitoring:** Core Web Vitals from the `web-vitals` library (or the error reporter's RUM), broken down by route, device class and release. The p75 drives the performance NFRs.
- **Analytics.**
  - Events come from the tracking plan, with `snake_case` names and documented parameters.
  - Analytics is gated by consent and carries no PII.
- **Logs.** `console.warn` and `console.error` only; no `console.log` in production code (lint enforces it).
- **Correlation IDs.** The HTTP client sends or reads a request-ID header, and error reports include it, so a user's failure can be traced in the backend.
- **Release dashboard:** error-free sessions, error rate and Web Vitals for each release. It drives the rollout and halt decisions.
