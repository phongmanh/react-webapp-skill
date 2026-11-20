# Security & privacy reference

Organised by OWASP ASVS chapter, from the frontend's side. The backend owns most ASVS controls; this list is what the web client must do and what it must not undermine.
- **L1** applies to every app.
- Items marked **(L2)** apply when the app handles sensitive data (finance, health, identity) or admin functions.

Choose the level in Phase 1 and verify it in Phase 5.

## The ground rule for secrets
- **The bundle is public.** Every file the browser downloads, including every `VITE_*` variable, can be read by anyone.
- **Valuable keys stay on the server.** API keys for paid or privileged services never ship in the app; the backend (or a BFF) holds them and calls the service.
- **Build-time config** (base URLs, public keys such as a publishable payments key) comes from CI environment variables, typed in `vite-env.d.ts`, never from Git. `.env*.local` is git-ignored.

## Sessions and authentication
- **Prefer cookies set by the backend:** `HttpOnly; Secure; SameSite=Lax` (or `Strict`), scoped to the API's host. JavaScript can't read them, so XSS can't steal them.
- **If tokens must live in the browser** (a third-party API with bearer tokens), keep the access token in memory only, use short lifetimes with refresh-token rotation, and record the trade-off in an ADR. Never in `localStorage`.
- **Sign-in** goes through the identity provider's redirect flow (OAuth 2.1 / OIDC with PKCE), never a password form inside an iframe or pop-up you don't control.
- **Refresh** is single-flight: when many requests get `401` at once, one refresh runs and the rest wait for it; if it fails, sign the user out and keep the URL to return to.
- **Sign-out** clears the query cache, persisted browser state and any in-memory tokens, and calls the backend to end the session.
- **Re-authenticate** before high-value actions (L2): changing email, password or MFA, payments, deleting the account.
- **Authorization is enforced on the server.** Client-side guards and hidden buttons are UX only.

## CSRF and cross-origin
- With cookie sessions, protect state-changing requests: `SameSite` cookies plus a CSRF token or a custom header the backend checks (e.g. `X-Requested-With`), and no state changes on `GET`.
- **CORS** is configured on the backend with an explicit origin list, never `*` with credentials.
- **`postMessage`:** check `event.origin` against an allow-list and parse `event.data` with a schema; send with an explicit `targetOrigin`, never `'*'`.

## Output encoding and XSS
- React escapes text by default. Keep it that way:
  - no `dangerouslySetInnerHTML`, unless the HTML is sanitised with DOMPurify and an ADR records why;
  - no user-controlled values in `href`, `src`, `style` or `action` without validation: allow `https:` (and `mailto:` where needed), reject `javascript:` and `data:`;
  - no `eval`, `new Function` or string `setTimeout`.
- **Markdown or rich text** from users is rendered by a library configured to drop raw HTML, or sanitised.
- **Open redirects:** a `returnTo` or `next` parameter is accepted only as a same-origin relative path.

## Security headers and CSP
Set at the host or CDN, verified on the deployed build ([project setup](project-setup.md#hosting)):
- `Content-Security-Policy`: start from `default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'`, then add only the origins the architecture lists (API, identity provider, error reporter, analytics). No `'unsafe-inline'` scripts; Vite's production build doesn't need them. Consider `report-to` for violations.
- `Strict-Transport-Security: max-age=63072000; includeSubDomains` (and `preload` once you're sure).
- `X-Content-Type-Options: nosniff`.
- `Referrer-Policy: strict-origin-when-cross-origin`.
- `Permissions-Policy` that switches off every feature the app doesn't use (camera, microphone, geolocation…).
- `Cross-Origin-Opener-Policy: same-origin` unless a pop-up flow needs otherwise.
- **Subresource Integrity** on any script or stylesheet loaded from a third-party CDN, or self-host it.

## Data in the browser
- **Never store** tokens, passwords, full card numbers or sensitive personal data in `localStorage`, `sessionStorage`, IndexedDB or the Cache API.
- **What is stored** is parsed with a schema on read, versioned, and cleared on sign-out.
- **Sensitive screens (L2):** `Cache-Control: no-store` on their API responses, and no sensitive data in URLs (they end up in history, logs and `Referer`).
- **Clipboard:** write only on a user action; never read without a clear need and a permission prompt.

## Dependencies and supply chain
- Commit the lockfile; CI installs with `npm ci`.
- Run `npm audit --audit-level=high` (or an equivalent scanner) in CI and fix advisories promptly.
- Vet each new dependency before adding it: maintenance, downloads, size, licence, install scripts. A runtime dependency the architecture doesn't list is a CR.
- Prefer self-hosting third-party scripts and fonts; each external origin is a CSP entry and a privacy disclosure.
- A secrets scan runs in CI (e.g. gitleaks) to catch keys before they ship.

## Error handling and logging
- Error messages shown to users never include stack traces, internal IDs or raw server messages; the request ID is fine.
- Error reports and logs carry no PII, tokens or form contents. Scrub URLs and breadcrumbs.
- Source maps go to the error reporter, not to the public host.

## Privacy
- **Minimise.** Collect the least data needed, and set a retention period for each data type.
- **Consent** comes before non-essential cookies, analytics or ad scripts load, where the law requires it (e.g. GDPR, ePrivacy). Rejecting is as easy as accepting.
- **No PII** in analytics events, URLs, logs or error reports.
- **Disclosures.** The privacy policy and cookie notice match the data inventory, including what third-party scripts collect. Link the privacy policy from every page footer.
- **Account deletion and data export,** if the app has accounts and the law requires them.
- **Transparency.** At the point of collection, say what's collected and why.

## Quick check for reviewers
- Secrets or keys in code or `VITE_*` variables?
- `dangerouslySetInnerHTML`, or user input in `href`/`src`?
- Tokens in browser storage?
- A new external origin without a CSP entry and a privacy review?
- PII in logs, analytics or URLs?
- A state-changing request without CSRF protection?
- A new dependency without a vetting note?
