# EVIDENCE — FE-030

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-13 (2026-09-10T10:20:16Z)
- Deliverable: admin auth store + `/login` view + generalised auth route guard.
- Files touched:
  - `web/frontend/src/stores/auth.ts` (new)
  - `web/frontend/src/views/LoginView.vue` (new)
  - `web/frontend/src/views/AdminView.vue` (scaffold + logout)
  - `web/frontend/src/router/index.ts` (guard + `meta`)
  - `web/frontend/tests/unit/auth.test.ts` (new)
- Commands run + output:

```
$ bun run test               # final batch run (16 files incl. parallel peers)
 ✓ tests/unit/auth.test.ts (12 tests)
 Test Files  16 passed (16)
      Tests  176 passed (176)

# Transient note: two mid-batch runs showed 4 failures in files owned by
# concurrent agents (tests/unit/decor-audit.test.ts [FE-014] and
# tests/unit/question-nav.test.ts [FE-024]); both are outside FE-030 scope and
# were green again once those agents finished. auth.test.ts passed 12/12 in every
# run.

$ bunx tsc --noEmit
(no output — success)

$ bunx vue-tsc --noEmit
(no output — success)

$ bun run lint
(src/components/Icon.vue 25:5 warning vue/require-default-prop — pre-existing,
 file outside FE-030 scope; 0 errors)

$ bunx prettier --check src/stores/auth.ts src/views/LoginView.vue src/views/AdminView.vue src/router/index.ts tests/unit/auth.test.ts
All matched files use Prettier code style!
```

### Store API (`useAuthStore`, id `auth`)
- State: `authenticated: boolean`, `roles: string[]`, `loading: boolean`,
  `error: string | null`, `initialized: boolean`.
- Getters: `isAuthenticated`, `isAdmin` (roles includes `admin`).
- Actions:
  - `login(password): Promise<boolean>` → `POST /api/admin/login`; on success sets
    `authenticated`/`roles: ['admin']` and stores the returned bearer token via
    `setAdminToken`; on failure clears session and records `error`.
  - `check(): Promise<boolean>` → `GET /api/admin/check`; resolves the cookie session;
    clears any stale bearer token when unauthenticated. Sets `initialized`.
  - `logout(): Promise<void>` → `POST /api/admin/logout`, then always clears local
    session state (even if the request rejects).
  - `hasRole(role)`, `hasAnyRole(roles)` for FS-002 role checks.
- Cookie/bearer handling (acceptance 2): the shared `apiRequest` client already sends
  `credentials: 'include'` (httpOnly `admin_token` cookie) and attaches `Bearer` when a
  token is registered; the store registers the login token and clears it on logout /
  unauthenticated check.

### Guard behavior (`src/router/index.ts`)
- Typed `RouteMeta`: `{ requiresAuth?: boolean; roles?: string[] }`.
- `authGuard`: public routes pass through untouched (no backend probe); `requiresAuth`
  routes lazily call `auth.check()` once (`initialized`), then redirect to
  `{ name: 'login', query: { redirect: to.fullPath } }` when unauthenticated or when the
  role set is not satisfied. `/admin` uses `meta: { requiresAuth: true, roles: ['admin'] }`.
- `LoginView` uses the `?redirect=` path (same-origin only) as the post-login destination;
  `AdminView` signs out to `/login`. Feedback uses the read-only `useToast` composable.

- Screenshots: n/a (browser legs deferred to host).
- Test cases executed (see TESTPLAN.md): T1 PASS (unit + router), T2 PASS (unit), T3 PASS (unit).
- Self-check against acceptance criteria:
  1. unauthenticated `/admin` redirects to login — PASS (router guard returns `/login`
     with `?redirect=/admin`; router push test asserts `currentRoute.name === 'login'`).
  2. cookie/bearer handled by client — PASS (client sends `credentials:'include'`;
     `auth.login` stores the bearer token, `logout`/failed check clear it).
  3. role guard generalized for FS-002 — PASS (`meta.roles` + `hasAnyRole`, typed
     `RouteMeta` augmentation; tests cover allow/deny).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
