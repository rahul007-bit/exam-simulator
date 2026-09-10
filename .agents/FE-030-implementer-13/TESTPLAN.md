# TESTPLAN — FE-030

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-030` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e / unit-router | `authGuard` on `{ requiresAuth, roles:['admin'] }` with `check=false`; `router.push('/admin')` | redirect to `/login?redirect=/admin` | PASS — `tests/unit/auth.test.ts` "redirects … /admin to /login"; router integration test asserts `currentRoute.name === 'login'` | |
| T2 | unit | `auth.login('wrong')` (401) then `auth.login('secret')` (200) | error set/return false then authenticated `true` | PASS — login failure + success tests; `error === 'Invalid admin password'` | |
| T3 | unit / integration | `auth.logout()` then `auth.check()` / `adminCheck` | `authenticated=false` | PASS — logout test clears token/roles; check-unauthenticated test returns false | |

## Edge cases / additions
- Login success stores the bearer token (`getAdminToken() === 'tok-123'`) and sends
  `POST /api/admin/login` with `{ password }`, `credentials: 'include'`.
- `check()` clears a stale bearer token when `/api/admin/check` is unauthenticated.
- `logout()` clears local state even when the network request rejects.
- Public routes (`meta: {}`) return `true` without calling `fetch`.
- Role helpers: `hasAnyRole([]) === true`, unknown role denied.
- Safe redirect: `?redirect=` only honoured when it starts with `/` and is not
  protocol-relative (`//host`); otherwise falls back to `/admin`.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commit; batch).
- Host: Windows / bun 1.x, Vitest 3.2.7 + jsdom.
- Browser(s): Playwright browser legs DEFERRED to the platform host (PROTOCOL §6).

## Verdict
- Implementer: PASS, 2026-09-10T10:20:16Z
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
