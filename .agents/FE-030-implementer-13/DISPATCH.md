# DISPATCH — FE-030

## 2026-09-10T10:20:16Z
You are assigned task **FE-030** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-030-implementer-13`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
vue-router guard + `/login` flow using `/api/admin/login`, `/api/admin/logout`,
`/api/admin/check`, backed by a new `auth` Pinia store.

### Acceptance criteria
1. Unauthenticated `/admin` redirects to `/login`; after login returns to the intended path.
2. The API client's cookie and bearer-token handling is driven by the store.
3. The guard is generalised (`meta: { requiresAuth, roles }`) for FS-002 roles.

### Verification method
- `bun run test` (unit suite incl. `tests/unit/auth.test.ts`)
- `bunx tsc --noEmit` / `bunx vue-tsc --noEmit`
- `bun run lint`
- Manual/e2e (host): bad password → error toast; good password → `/admin`; logout → redirect.
- `curl` (host): `GET /api/admin/check` before/after logout → `authenticated:false`.

### Constraints
- One focused change; strict file ownership (parallel batch).
- Preserve parity behavior (cookie + bearer token, `/api/admin/*` endpoints).
- Update `EVIDENCE.md` with proof; the orchestrator owns `tasks.json`.
