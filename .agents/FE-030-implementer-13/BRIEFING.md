# BRIEFING — FE-030

## Mission
Add the admin auth foundation: an `auth` Pinia store around the admin login/check/logout
endpoints, a `/login` view with toast feedback, and a generalised `requiresAuth`/`roles`
route guard so unauthenticated `/admin` visits bounce to `/login` and return after sign-in.

## 🔒 Identity
- Task: FE-030
- Role: implementer
- Working directory: .agents/FE-030-implementer-13
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-012 (UI primitives) — verified.
- **Acceptance criteria:**
  1. unauthenticated `/admin` redirects to login
  2. cookie/bearer handled by client
  3. role guard generalized for future FS-002
- **Test cases:** (canonical in `tasks.json`; results in TESTPLAN.md)
  1. T1 — visit `/admin` unauthenticated → redirect to login
  2. T2 — bad creds then good creds → error toast then dashboard
  3. T3 — logout then `/api/admin/check` → `authenticated=false`
- **Verifier:** independent agent (not implementer-13)

## Key constraints
- Follow `decisions.md`; no contradiction with accepted decisions (D-003 palette, D-009 future auth).
- Strict behavioral parity (D-007): cookie + bearer auth matches `web/static/js/admin.js`.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `src/stores/auth.ts`, `src/views/LoginView.vue`, `src/views/AdminView.vue`,
  `src/router/index.ts`, `tests/unit/auth.test.ts`

## Artifact index
- `.agents/FE-030-implementer-13/DISPATCH.md`
- `.agents/FE-030-implementer-13/progress.md`
- `.agents/FE-030-implementer-13/EVIDENCE.md`
