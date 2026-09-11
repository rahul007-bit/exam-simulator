# BRIEFING — FE-040 (part 2: cutover)

## Mission
Complete FE-040 by deleting the legacy static UI and serving only the built Vue
SPA from `web/dist`, so `web/server.py` has a single, honest frontend path.

## 🔒 Identity
- Task: FE-040 (cutover half)
- Role: implementer
- Working directory: .agents/fe040-cutover-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-040 part 1 (`fe040-purge-implementer`) — legacy refs purged from `web/frontend/**`.
- **Acceptance criteria:** (mirror the task entry)
  1. `web/static/**` deleted and staged.
  2. `web/server.py` serves only `web/dist`: `/admin` + catch-all from SPA; 503 when build absent.
  3. Unknown `api`/`ws`/`novnc` → 404.
  4. Tools/docs updated; no legacy fallback copy.
  5. Backend cutover test passes.
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 audit — zero legacy references.
  2. T2 host/browser — SPA served for app routes (DEFERRED: host-only).
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md`; strict behavioral parity (D-007) — preserve WS contracts
  and URL/token routing.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/static/**` (delete), `web/server.py`,
  `tools/build-frontend.sh`, `tools/start-web.sh`, `PLATFORM_SETUP.md`,
  `README.md` (if needed), `tests/test_frontend_cutover.py`

## Artifact index
- `.agents/fe040-cutover-implementer/DISPATCH.md`
- `.agents/fe040-cutover-implementer/progress.md`
- `.agents/fe040-cutover-implementer/EVIDENCE.md`
- `.agents/fe040-cutover-implementer/TESTPLAN.md`
