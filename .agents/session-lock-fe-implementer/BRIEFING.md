# BRIEFING — session-lock-fe

## Mission
Implement the frontend half of the per-session owner lock in the Vue 3 SPA: a
stable per-browser `cka_client_id` cookie + `X-Client-Id` header, candidate-token
resume across refresh, a locked-session screen, and E2E hardening so tests can
never proxy to a live backend.

## 🔒 Identity
- Task: session-lock-fe
- Role: implementer
- Working directory: .agents/session-lock-fe-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** backend owner-lock contract (`web/server.py`, concurrent agent).
- **Acceptance criteria:**
  1. `cka_client_id` cookie ensured/stable + `X-Client-Id` on every `apiRequest`.
  2. Candidate token persisted under `cka:candidate-token`; resume on refresh.
  3. Locked inactive session (`locked:true`) renders a dedicated card; workspace hidden.
  4. Playwright dev server always fresh, proxying to a dead port.
  5. New unit test for cookie helper + `isLocked`; all existing tests green.
- **Test cases:** see TESTPLAN.md.
- **Verifier:** independent agent.

## Key constraints
- Do not touch `web/server.py`, `src/components/**`, styles, fonts, docker, other tests.
- No commit/amend/push. Do not run `scripts/agents_board.py`.

## Pointers
- Contract: shared with backend agent (session-lock).
- Files in scope: `web/frontend/src/api/{client,session}.ts`,
  `src/stores/{session,index}.ts`, `src/views/CandidateView.vue`,
  `playwright.config.ts`, `tests/unit/session-lock.test.ts`.

## Artifact index
- `.agents/session-lock-fe-implementer/DISPATCH.md`
- `.agents/session-lock-fe-implementer/progress.md`
- `.agents/session-lock-fe-implementer/EVIDENCE.md`
