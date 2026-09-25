# BRIEFING — FE-003

## Mission
Serve the built Vue 3 SPA (`web/dist`) from FastAPI with an SPA fallback, route
`/admin` to the SPA, and wire the frontend build into `tools/start-web.sh` and the
systemd unit — while keeping every `/api`, `/ws` and `/novnc` route unchanged and
preserving the legacy `web/static` UI as the fallback until FE-040.

## 🔒 Identity
- Task: FE-003
- Role: implementer
- Agent: implementer-1
- Working directory: `.agents/FE-003-implementer-1`
- Branch: `feature/frontend-vue-migration`

## Task contract
- **Depends on:** FE-001 (verified)
- **Acceptance criteria:**
  1. `GET /` and `GET /admin` return the SPA index.
  2. All existing `/api` and `/ws` routes unchanged and registered BEFORE the SPA
     catch-all so they take precedence.
  3. The `/novnc` StaticFiles mount is preserved.
  4. Build on deploy produces `web/dist` without committing it.
- **Test cases:**
  1. T1 `curl -s localhost:3000/` — SPA index returned (host-only).
  2. T2 `curl -s -o /dev/null -w '%{http_code}' localhost:3000/api/session` — 200 (host-only).
  3. T3 `python scripts/verify_platform_api.py` — pass (host-only).
- **Verifier:** independent agent (not implementer-1)

## Key constraints
- Follow `decisions.md` — D-005 (build on deploy, `web/dist` not committed),
  D-007 (strict parity: no API/WS handler changes).
- Do not self-certify; a different agent verifies.
- Only touch FE-003's scope: `web/server.py`, `tools/start-web.sh`,
  `tools/build-frontend.sh`, `tools/setup-platform.sh`, `PLATFORM_SETUP.md`.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md` (§4 Backend glue)
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/server.py`, `tools/start-web.sh`, `tools/build-frontend.sh`,
  `tools/setup-platform.sh`, `PLATFORM_SETUP.md`

## Environment note
The backend imports Linux-only modules (`pty`, `fcntl`, `termios`) and live core
services; FastAPI/uvicorn are not installed on this Windows workstation. T1–T3
are therefore **host-only DEFERRED**. Local equivalents: `py_compile`, an AST
route-order audit, the frontend build, and shell-script branch tests.

## Artifact index
- `.agents/FE-003-implementer-1/DISPATCH.md`
- `.agents/FE-003-implementer-1/progress.md`
- `.agents/FE-003-implementer-1/EVIDENCE.md`
- `.agents/FE-003-implementer-1/TESTPLAN.md`
- `.agents/FE-003-implementer-1/route_order_audit.py`
