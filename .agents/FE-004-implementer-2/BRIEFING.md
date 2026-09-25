# BRIEFING — FE-004

## Mission
Deliver a typed API client and Pinia base stores (session, timer, presets) for the
existing FastAPI backend, so later candidate/admin tasks build on typed state and a
single typed fetch layer instead of ad-hoc `fetch` calls.

## 🔒 Identity
- Task: FE-004
- Role: implementer
- Agent: implementer-2
- Working directory: `.agents/FE-004-implementer-2`
- Branch: `feature/frontend-vue-migration`

## Task contract
- **Depends on:** FE-003 (verified)
- **Acceptance criteria:**
  1. types generated from `/openapi.json`
  2. client covers session, timer, presets, actions endpoints
  3. stores expose typed state and actions; smoke test hits `/api/session`
- **Test cases:**
  1. `T1` (unit): `npm run gen:api && npx tsc --noEmit` → types generate; exit 0
  2. `T2` (integration): session store `fetchSession()` → typed `/api/session` data populated
- **Verifier:** independent-agent (may not be implementer-2)

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): WS contracts (`timer_tick`, …) and URL/token routing
  preserved; this task only adds a client + stores, no UI/parity surface changed.
- Design the client to send credentials for future auth (FS-002): every request uses
  `credentials: 'include'`; bearer token support is available.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md` (§3 architecture)
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/openapi.json`, `web/frontend/scripts/gen-api.mjs`,
  `web/frontend/src/api/**`, `web/frontend/src/stores/**`, `web/frontend/src/main.ts`,
  `web/frontend/package.json`, `web/frontend/vitest.config.ts`,
  `web/frontend/tests/unit/stores.test.ts`, `web/frontend/tests/setup.ts`

## Artifact index
- `.agents/FE-004-implementer-2/DISPATCH.md`
- `.agents/FE-004-implementer-2/progress.md`
- `.agents/FE-004-implementer-2/EVIDENCE.md`
- `.agents/FE-004-implementer-2/TESTPLAN.md`
