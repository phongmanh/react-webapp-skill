# Feature design: <Feature>
<!-- About 24 KB at most, so a dependent feature can read it in one Read. Signatures and types, not implementations; cite architecture sections instead of restating them. Other features read only §2's public API. -->

| FR IDs | Owner | Status | UI designs |
|---|---|---|---|
| FR-001, FR-002 | <developer> | Draft | <Figma link, or "house style"> |

## 1. Routes and screens
| Route | Screen | Layout | Auth | States | URL state |
|---|---|---|---|---|---|
| `/notes` | Notes list | Shell | Signed in | Loading, Empty, Error, Success | `?q=`, `?cursor=` |

### <Screen>: spec
| Field | Content |
|---|---|
| Purpose | <one sentence, FR IDs> |
| Primary action | <e.g. "Create note" (link to `/notes/new`)> |
| Layout | <shell, max width, columns per breakpoint, what collapses below `lg`> |
| Content order | <header → notices → filters → list → load more> |
| Focus | <arrival: `h1`; after Load more: first new row; after delete: the list heading> |
| Copy | <catalogue keys the acceptance criteria fix> |

### <Screen>: view state and actions
```ts
type NotesViewState =
  | { status: 'loading' }
  | { status: 'error'; error: AppError }
  | { status: 'empty' }
  | { status: 'success'; notes: readonly Note[]; hasMore: boolean }

type NotesContentProps = {
  state: NotesViewState
  onRetry: () => void
  onLoadMore: () => void
}
```
Survives reload: <what comes from the URL; what is refetched>

## 2. Contracts and schemas
```ts
export const NoteSchema = z.object({ id: z.string(), title: z.string().min(1).max(120), body: z.string(), updatedAt: z.iso.datetime() })
export type Note = z.infer<typeof NoteSchema>
export const NoteListSchema = z.object({ items: z.array(NoteSchema), nextCursor: z.string().nullable() })
```
Public API (`features/notes/index.ts`): <exports other features and routes may use>

## 3. Data
| Endpoint | Request | Response | Errors |
|---|---|---|---|
| `GET /v1/notes?q&cursor` | — | `NoteList` | 401, 5xx |
| `POST /v1/notes` | `NewNote` | `Note` (201) | 400 (field errors), 401, 409 |

```ts
export const noteKeys = { all: ['notes'] as const, list: (f: NoteFilters) => [...noteKeys.all, 'list', f] as const }
export function useNotes(filters: NoteFilters): UseQueryResult<NoteList>
export function useCreateNote(): UseMutationResult<Note, unknown, NewNote>
```
- **Freshness:** `staleTime` <n> s; refetch on <…>
- **Invalidation:** <which keys after which mutation>
- **Optimistic updates:** <none / where, with rollback>
- **Browser storage:** <none / keys and schema version>

## 4. Forms
| Field | Type and `autocomplete` | Rules (schema) | Error shown | Server error mapping |
|---|---|---|---|---|
| Title | text | required, ≤ 120 | on blur and submit | `title` field error from 400 |

Submit: <pending state, success announcement, where the user lands>

## 5. Errors
| AppError | Message (catalogue key) | UI behaviour |
|---|---|---|
| network | `error.network` | Error state with Retry; or a notice if cached notes are shown |
| unauthorized | `error.sessionExpired` | Go to sign-in, return here after |
| conflict | `error.conflict` | Notice; keep the user's input; offer Reload |

## 6. Analytics
| Event | Parameters | Trigger |
|---|---|---|

## 7. Accessibility and i18n
- Landmarks and headings
- Labels and accessible names for icon buttons
- Live-region announcements
- Focus after each transition (see the screen spec)
- New catalogue keys and plurals
- RTL and long-language notes

## 8. Test cases
| ID | Level | FR | Case |
|---|---|---|---|
| IT-001 | Integration | FR-001 | Loading then success lists the notes as links |
| IT-002 | Integration | FR-001 | A 500 shows the error with Retry; Retry loads the notes |
| IT-003 | Integration | FR-001 | No notes shows the empty state with "Create note" |
| UI-001 | E2E | FR-001 | A user lists notes and opens one; focus lands on the `h1` |
| UI-002 | E2E + axe | NFR-A11Y-01 | `/notes` has no WCAG 2.2 AA violations, loaded and empty |

## 9. PR slice plan
| # | PR | Layer | Est. changed lines |
|---|---|---|---|
| 1 | Schemas, helpers + unit tests | Schemas | ~150 |
| 2 | API functions, query keys, hooks, MSW handlers + tests | Data | ~300 |
| 3 | Presentational components for each state + tests | Components | ~300 |
| 4 | Container, route, nav item, catalogue keys | Wiring | ~200 |
| 5 | E2E flow + axe scans | Test | ~120 |

## 10. Open questions
- <…>
