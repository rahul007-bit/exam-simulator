# EVIDENCE — FS-002 Auth frontend (/login, auth store, guards)

Agent: opencode. Date: 2026-09-11. Depends on FS-001 (verified).

## Deliverable
- `web/frontend/src/api/auth.ts` — typed `authLogin`, `authLogout`, `authMe`;
  exported as `authApi` from `api/index.ts`.
- `web/frontend/src/stores/auth.ts` — extended (backward compatible): state
  `{authenticated, roles, username, loading, error, initialized}`; `login(
  username,password)` → `/api/auth/login`; legacy `loginAdmin(password)` kept;
  `check()` tries `/api/auth/me` then falls back to `/api/admin/check`;
  `logout()` calls both endpoints; `hasRole`/`hasAnyRole`; `USER_ROLE` added.
- `web/frontend/src/views/LoginView.vue` — username + password form.
- `web/frontend/src/router/index.ts` — `/dashboard` and `/exam/:sessionId`
  guarded `{requiresAuth, roles:['admin','user']}`; `/admin` stays admin.
- `web/frontend/openapi.json` — 5 new paths + schemas; `bun run gen:api`
  regenerated `src/api/schema.d.ts`.
- Acceptance: login persists session (httponly cookie + `/me` rehydrate) ✔;
  guards by role ✔; logout clears state ✔.

## Tests / verification (orchestrator consolidated pass)
- `bun run lint` clean; `bunx vue-tsc --noEmit` clean.
- `bun run test` → 22 files / 235 tests pass (auth.test.ts 17).
- `bun run build` → success.
- `npx playwright test` → 21 passed.
- Note: live role flows against the real backend still run during FE-044.
