# EVIDENCE — FS-005 User dashboard (own exams only)

Agent: opencode. Date: 2026-09-11. Depends FS-002 + FS-004 (verified).

## Deliverable
- `web/frontend/src/views/DashboardView.vue` (new) — lists only the signed-in
  user's assignments via `listMyAssignments()` (`GET /api/assignments`); renders
  preset, status badge, created date, Start/Resume; empty + error + loading
  states; Refresh. Start navigates to `/?token=<token>` (no new endpoint).
  Never calls a preset/question catalog endpoint.
- `web/frontend/src/router/index.ts` — `/assignments` renders DashboardView
  (orchestrator wiring), `{requiresAuth, roles:['admin','user']}`.
  **Route renamed `/dashboard` → `/assignments`**: Traefik owns
  `PathPrefix('/dashboard')` for its own secured dashboard, so the SPA route was
  shadowed. Dashboard also redirects to `/login?redirect=/assignments` when the
  user session is absent (a legacy admin cookie can satisfy the route guard
  without a user auth session).
- `web/frontend/tests/unit/dashboard.test.ts` — 8 tests incl. "no catalog call".
- Acceptance: no full catalog exposed ✔; start assigned exam from dashboard ✔.

## Tests / verification (orchestrator consolidated pass)
- Frontend: lint + `vue-tsc` clean; `bun run test` → 24 files / 250 tests.
- `bun run build` + `npx playwright test` → 21 passed.
