# Code patterns

This is the canonical TypeScript and React for each concern. When new code follows these shapes, every feature reads the same and a reviewer can compare a PR against this one page. The project's own rules override it. Some imports are omitted. The example feature is a notes list.

## TypeScript style
- **Strict, with no escape hatches:** no `any` (use `unknown` and narrow), no `@ts-ignore`, and `@ts-expect-error` only with a written reason.
- **Types come from schemas:** `type Note = z.infer<typeof NoteSchema>`. Don't write a type by hand next to a schema.
- **Discriminated unions** for states, results and events; a `switch` over one ends with an exhaustive `never` check.
- **No `enum` or `namespace`** (`erasableSyntaxOnly`). Use a union of literals or an `as const` object.
- **`satisfies`** for config objects, so the shape is checked and the literal types are kept.
- **`import type`** for type-only imports (`verbatimModuleSyntax`).
- **No `!`.** Guard and throw with a message: `if (!root) throw new Error('#root not found')`.
- **Explicit return types** on exported functions and hooks that form a module's public API.
- **Names say what, not how:** `useNotes()`, `formatUpdatedAt()`, `NotesViewState`. Booleans read as questions: `isPending`, `hasMore`. Handlers are `handleX`; callback props are `onX`.
- **No magic values:** `SCREAMING_SNAKE_CASE` constants; the catalogue for anything the user sees.
- **Files:** `PascalCase.tsx` for components (one exported component per file), `camelCase.ts` otherwise.
- **Comments** explain *why*, never *what*.

## Schemas (`features/notes/schemas.ts`)
```ts
import { z } from 'zod'

export const NoteSchema = z.object({
  id: z.string(),
  title: z.string().min(1).max(120),
  body: z.string(),
  updatedAt: z.iso.datetime(),
})
export type Note = z.infer<typeof NoteSchema>

export const NoteListSchema = z.object({ items: z.array(NoteSchema), nextCursor: z.string().nullable() })
export type NoteList = z.infer<typeof NoteListSchema>

export const NewNoteSchema = NoteSchema.pick({ title: true, body: true })
export type NewNote = z.infer<typeof NewNoteSchema>
```
- Forms reuse the API schema (or a `.pick` / `.extend` of it), so client and server validation agree.
- Objects tolerate unknown fields by default; an enum-like field the backend may extend uses `z.enum([...]).catch('other')`.

## HTTP client (`lib/http.ts`)
```ts
import type { z } from 'zod'

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'
const TIMEOUT_MS = 15_000

export class HttpError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | undefined,
    readonly requestId: string | undefined,
    message: string,
  ) {
    super(message)
    this.name = 'HttpError'
  }
}

async function request<T>(path: string, schema: z.ZodType<T>, init: RequestInit = {}): Promise<T> {
  const timeout = AbortSignal.timeout(TIMEOUT_MS)
  const signal = init.signal ? AbortSignal.any([init.signal, timeout]) : timeout
  const headers = new Headers(init.headers) // never spread HeadersInit; it may be an array
  if (init.body !== undefined) headers.set('Content-Type', 'application/json')
  const res = await fetch(`${BASE_URL}${path}`, { ...init, signal, headers, credentials: 'include' })
  if (!res.ok) {
    const requestId = res.headers.get('X-Request-Id') ?? undefined
    const code = await res
      .json()
      .then((b: unknown) => (typeof b === 'object' && b && 'code' in b ? String(b.code) : undefined))
      .catch(() => undefined)
    throw new HttpError(res.status, code, requestId, `${init.method ?? 'GET'} ${path} failed: ${res.status}`)
  }
  const body: unknown = res.status === 204 ? undefined : await res.json()
  return schema.parse(body)
}

export const http = {
  get: <T>(path: string, schema: z.ZodType<T>, signal?: AbortSignal) => request(path, schema, { signal }),
  post: <T>(path: string, body: unknown, schema: z.ZodType<T>) =>
    request(path, schema, { method: 'POST', body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown, schema: z.ZodType<T>, etag?: string) =>
    request(path, schema, {
      method: 'PATCH',
      body: JSON.stringify(body),
      headers: etag ? { 'If-Match': etag } : undefined,
    }),
}
```

## Error mapping (`lib/errors.ts`)
```ts
import { ZodError } from 'zod'
import { HttpError } from './http'

export type AppError =
  | { kind: 'network' }
  | { kind: 'unauthorized' }
  | { kind: 'forbidden' }
  | { kind: 'notFound' }
  | { kind: 'conflict' }
  | { kind: 'validation'; fields: Record<string, string> }
  | { kind: 'rateLimited'; retryAfterSeconds?: number }
  | { kind: 'server'; requestId?: string }
  | { kind: 'unknown'; requestId?: string }

export function toAppError(error: unknown): AppError {
  if (error instanceof HttpError) {
    switch (error.status) {
      case 401: return { kind: 'unauthorized' }
      case 403: return { kind: 'forbidden' }
      case 404: return { kind: 'notFound' }
      case 409:
      case 412: return { kind: 'conflict' }
      case 429: return { kind: 'rateLimited' }
      default: return error.status >= 500 ? { kind: 'server', requestId: error.requestId } : { kind: 'unknown', requestId: error.requestId }
    }
  }
  if (error instanceof ZodError) return { kind: 'unknown' } // a contract bug: also reported
  if (error instanceof TypeError || (error instanceof DOMException && error.name === 'TimeoutError')) return { kind: 'network' }
  return { kind: 'unknown' }
}

export function errorMessageKey(error: AppError): MessageKey {
  switch (error.kind) {
    case 'network': return 'error.network'
    case 'unauthorized': return 'error.sessionExpired'
    case 'forbidden': return 'error.forbidden'
    case 'notFound': return 'error.notFound'
    case 'conflict': return 'error.conflict'
    case 'validation': return 'error.validation'
    case 'rateLimited': return 'error.rateLimited'
    case 'server':
    case 'unknown': return 'error.generic'
    default: {
      const unreachable: never = error
      return unreachable
    }
  }
}
```
`MessageKey` is the union of catalogue keys from `lib/i18n`. Add one `case` per kind; never a catch-all that hides a new kind.

## Data hooks (`features/notes/api/`)
```ts
export const noteKeys = {
  all: ['notes'] as const,
  list: (filters: NoteFilters) => [...noteKeys.all, 'list', filters] as const,
  detail: (id: string) => [...noteKeys.all, 'detail', id] as const,
}

export function useNotes(filters: NoteFilters): UseQueryResult<NoteList> {
  return useQuery({
    queryKey: noteKeys.list(filters),
    queryFn: ({ signal }) => http.get(`/notes?${toSearch(filters)}`, NoteListSchema, signal),
  })
}

export function useCreateNote(): UseMutationResult<Note, unknown, NewNote> {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (note: NewNote) => http.post('/notes', note, NoteSchema),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: noteKeys.all }),
  })
}
```
- One query-key factory per feature; every key starts with the feature's root key, so one invalidation refreshes it all.
- QueryClient defaults are set once in `app/`: a deliberate `staleTime`, and `retry` that skips 4xx:
  ```ts
  retry: (count, error) => !(error instanceof HttpError && error.status < 500) && count < 2
  ```
- Optimistic updates only where a requirement asks for instant feedback, always with `onError` rollback.

## View state and components
A container turns query results into one view state; a presentational component renders it.
```tsx
type NotesViewState =
  | { status: 'loading' }
  | { status: 'error'; error: AppError }
  | { status: 'empty' }
  | { status: 'success'; notes: readonly Note[]; hasMore: boolean }

function toViewState(query: UseQueryResult<NoteList>): NotesViewState {
  if (query.isPending) return { status: 'loading' }
  if (query.isError) return { status: 'error', error: toAppError(query.error) }
  if (query.data.items.length === 0) return { status: 'empty' }
  return { status: 'success', notes: query.data.items, hasMore: query.data.nextCursor !== null }
}

export function NotesPage() {
  const [searchParams] = useSearchParams()
  const filters = parseNoteFilters(searchParams) // URL state, parsed with a schema
  const query = useNotes(filters)
  return <NotesContent state={toViewState(query)} onRetry={() => void query.refetch()} />
}

type NotesContentProps = { state: NotesViewState; onRetry: () => void }

export function NotesContent({ state, onRetry }: NotesContentProps) {
  const t = useT()
  switch (state.status) {
    case 'loading':
      return <output>{t('notes.loading')}</output>
    case 'error':
      return <ErrorPanel message={t(errorMessageKey(state.error))} onRetry={onRetry} />
    case 'empty':
      return <EmptyState title={t('notes.empty.title')} action={<LinkButton to="/notes/new">{t('notes.create')}</LinkButton>} />
    case 'success':
      return (
        <ul>
          {state.notes.map((note) => (
            <li key={note.id}>
              <NoteRow note={note} />
            </li>
          ))}
        </ul>
      )
    default: {
      const unreachable: never = state
      return unreachable
    }
  }
}
```
- Props are a named `XProps` type, destructured in the signature. No `React.FC`.
- Never define a component inside another component.
- Keys come from data IDs, never array indexes for lists that change.
- `{count > 0 && <List />}`, never `{count && <List />}`, which renders `0`.
- Pass intent callbacks (`onRetry`, `onDelete(id)`), not `setState` functions.
- Split a component at ~150 lines, by responsibility.

## Forms
```tsx
export function NoteForm({ onSaved }: { onSaved: (note: Note) => void }) {
  const t = useT()
  const createNote = useCreateNote()
  const form = useForm<NewNote>({ resolver: zodResolver(NewNoteSchema), mode: 'onTouched' })

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      onSaved(await createNote.mutateAsync(values))
    } catch (error) {
      const appError = toAppError(error)
      if (appError.kind === 'validation') {
        for (const [name, key] of Object.entries(appError.fields)) form.setError(name as keyof NewNote, { message: key })
      } else {
        form.setError('root', { message: errorMessageKey(appError) })
      }
    }
  })

  return (
    <form onSubmit={(e) => void onSubmit(e)} noValidate>
      {form.formState.errors.root && <Alert tone="error">{t(form.formState.errors.root.message as MessageKey)}</Alert>}
      <TextField label={t('notes.field.title')} error={form.formState.errors.title?.message} {...form.register('title')} />
      <Button type="submit" isPending={createNote.isPending}>{t('notes.save')}</Button>
    </form>
  )
}
```
- `shouldFocusError` (on by default) moves focus to the first invalid field after a failed submit.
- `TextField` renders a visible `<label>`, sets `aria-invalid`, and links the hint and error with `aria-describedby`.
- The submit button shows pending and is disabled while in flight, which prevents double submits.

## Routing (`app/router.tsx`)
```ts
export const router = createBrowserRouter([
  {
    path: '/',
    Component: AppShell,
    ErrorBoundary: RouteError,
    children: [
      { index: true, lazy: async () => ({ Component: (await import('@/routes/HomePage')).default }) },
      {
        path: 'notes',
        ErrorBoundary: RouteError,
        children: [
          { index: true, lazy: async () => ({ Component: (await import('@/routes/NotesPage')).default }) },
          { path: ':noteId', lazy: async () => ({ Component: (await import('@/routes/NoteDetailPage')).default }) },
        ],
      },
      { path: '*', lazy: async () => ({ Component: (await import('@/routes/NotFoundPage')).default }) },
    ],
  },
])
```
- Every route is lazy and sits under an `ErrorBoundary`, so a crash in one route leaves the shell working.
- `RouteError` recognises a failed dynamic import after a deploy and reloads once (guarded by a `sessionStorage` flag) instead of showing an error.
- Auth guards redirect for UX only. The server enforces authorization.
- The app shell's `RouteFocus` moves focus to the page `h1` and sets `document.title` after each navigation.

## Instead of … write …
| Instead of | Write | Why |
|---|---|---|
| `useEffect(() => setVisible(items.filter(...)), [items])` | `const visible = items.filter(...)` | Derive during render; no extra render or stale state |
| `useEffect(() => { fetch(...).then(setData) }, [])` | `useQuery(...)` | Caching, cancellation, retries and race safety |
| `const [user, setUser] = useState(query.data)` | Use `query.data` directly | Server state has one source of truth |
| `as Note` on a response | `NoteSchema.parse(body)` | A cast hides contract bugs |
| `<div onClick>` | `<button type="button" onClick>` | Keyboard and screen-reader support for free |
| `enum Status { ... }` | `const STATUSES = [...] as const; type Status = (typeof STATUSES)[number]` | `erasableSyntaxOnly` |
| `key={index}` | `key={item.id}` | Stable identity when items move |
| `localStorage.getItem('token')` | `HttpOnly` cookie set by the backend | XSS can't read it |
| `dangerouslySetInnerHTML={{ __html: html }}` | Render text, or sanitise with DOMPurify and an ADR | XSS |
| `'#1D6B48'` or `px-[13px]` in JSX | A token utility (`bg-primary`, `px-3`) | One design system |
