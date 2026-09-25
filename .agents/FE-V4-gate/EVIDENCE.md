# EVIDENCE — FE-V4 gate (M4 Admin) — independent audit

Auditor: independent subagent. Branch feature/frontend-vue-migration, HEAD e6b4273 (clean).
Scope: FE-030..FE-036 acceptance lists from `.agents/frontend-migration/tasks.json` checked against actual code.

## Test runs (re-executed by this audit)

| Command | Result |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest tests/test_auth_users.py tests/test_admin_users.py -q` | **34 passed** in 61.77s |
| `bun run lint` (web/frontend) | exit 0, no issues |
| `bunx vue-tsc --noEmit` | exit 0 |
| `bun run test` (vitest, jsdom) | **28 files, 283 tests passed** |
| `python scripts/agents_board.py --check` | `validation OK (48 tasks)` |

Browser/Playwright legs: DEFERRED per program command_notes (host-only); unit/audit legs executed.

## Per-task verification

### FE-030 — Admin auth guard and login — PASS
- Router guard `authGuard` at `web/frontend/src/router/index.ts:65` redirects unauthenticated `requiresAuth` routes to `{ name: 'login', query: { redirect } }`; `/admin` and `/admin/settings` both carry `meta: { requiresAuth: true, roles: ['admin'] }` (index.ts:34,58,60).
- Role guard generalised: `RouteMeta.roles?: string[]` + `auth.hasAnyRole(...)` (`src/stores/auth.ts:154`) — supports future FS-002 roles (index.ts:14-24 comment).
- Client login flow uses `/api/admin/login`, `/api/admin/logout`, `/api/admin/check` via typed functions in `src/api/admin.ts:20-38`; cookie/bearer handled by `apiRequest` client. LoginView reads `redirect` query (LoginView.vue:19-48).

### FE-031 — Admin sessions table and actions — PASS
- `src/composables/useAdminSessions.ts` + `src/views/AdminView.vue` list active/invite/archived sessions from `/api/admin/sessions` in the shared `DataTable` (sorting/filtering/pagination built-in, `page-size=10`).
- Actions terminate/reset/end hit `/api/admin/sessions/{id}/terminate|reset|end` gated by promise `useConfirm` dialog (AdminView.vue:188), results via `useToast`.
- `ACTIONS_BY_TYPE` (useAdminSessions.ts:40) restricts invite/archived rows to terminate.

### FE-032 — Admin config and resource forms — PASS
- `AdminConfigForm.vue` reflects `/api/admin/config` (default preset; `useAdminConfig.getAdminConfig`/`setAdminConfig`).
- `AdminResourceForm.vue` shows `/api/admin/resources` snapshot (`running_containers`, `max_concurrent_sessions`, memory, recommended max) and edits max concurrent sessions with `validateMaxSessions` (`useAdminConfig.ts`); invalid input shows inline error + emits `invalid` → toast (AdminSettingsView.vue:96-99) and does not save.
- Success feedback via toast (`onSavePreset`, `onSaveMaxSessions` in AdminSettingsView.vue:39-56).

### FE-033 — Admin create invite — PASS
- `useAdminInvites.ts` calls `/api/admin/sessions/create` (`api/admin.ts:47-52`), errors (incl. 429 capacity-limit detail) rethrow to the view → error toast (AdminSettingsView.vue:102-110).
- Copyable URL: `buildInviteUrl` absolute URL star in `AdminInviteForm.vue`, copy via `copyTextToClipboard` with success toast ("Invite link copied to clipboard!").

### FE-034 — Admin infrastructure table — PASS
- `AdminInfrastructureTable.vue` lists fleet nodes + Docker + Incus resources from `/api/admin/infrastructure` (`useAdminInfrastructure.ts:104-121`).
- Terminate calls `/api/admin/infrastructure/terminate` with `{kind,node,name}` (useAdminInfrastructure.ts:150-158), gated by `useConfirm` dialog (AdminInfrastructureTable.vue:190), per-row pending spinner, refresh removes the row.

### FE-035 — Admin live observe view — PASS
- `ObserveOverlay.vue` attaches only to an explicit `sessionId` prop; islands never mount when no concrete id ("No explicit session selected — observation is disabled to prevent attaching to a different candidate", ObserveOverlay.vue), reusing `NoVncFrame` (view-only) and `XTerm :session-id`.
- Reset/End available inside observe via `onReset`/`onEnd` → `useObserve.runAction` + confirm + toast; server-side cross-session enforcement is the backend WS 1008 close per code comment/notes.
- Admin notify (`notifySession` → `/api/admin/sessions/{id}/notify`) and review/replay present.

### FE-036 — Tighter dialog spacing + non-blocking per-row loading — PASS
- `useAdminSessions` tracks pending per-row via `pendingById: Map<string, SessionAction>`; `isRowPending(identifier)` is true only for the acting row; no global busy flag (useAdminSessions.ts:74-123).
- `DataTable :loading` is driven by `loading` (initial load only); post-mutation refresh uses `fetchSessions({ silent: true })` → `refreshing`, so the table stays populated (useAdminSessions.ts:126-150).
- Row Actions cell renders inline spinner + "Resetting…/Ending…/Terminating…" (AdminView.vue:45-58); other rows remain clickable (`onRowClick` has no global-busy guard).
- Only the affected row's dialog buttons are disabled (SessionActionsDialog.vue:113,158-172); toast + promise confirm retained; native `alert(`/`confirm(` audit: none (all matches are the `useConfirm` composable).
- Tighter spacing: Modal `p-4`/`mt-3`, ConfirmDialog `mb-1.5`/`mb-3`, SessionActionsDialog `gap-3`/`gap-y-1.5`/`pt-3` (per FE-036 EVIDENCE spacing table, still present in source).

## Verdict
All seven M4 tasks independently verified; backend (34) and frontend (lint + vue-tsc + 283 vitest) test legs pass. Gate FE-V4 marked verified via board CLI.
