# BRIEFING — FE-023

## Mission
Deliver a `useTimer` composable plus an updated timer store that consumes
`timer_tick` frames from the session WebSocket, keeps the countdown synced to the
server clock, falls back to polling `/api/timer` when disconnected, recovers on
reconnect, and exposes warning/critical states using colour only (AA-safe tokens).

## 🔒 Identity
- Task: FE-023
- Role: implementer
- Working directory: .agents/FE-023-implementer-10
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-004 (verified)
- **Acceptance criteria:** (mirror the task entry)
  1. timer stays in sync with `server_timestamp`
  2. reconnects and continues correctly
  3. warning/critical styles use colour only
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 (integration): start exam, watch timer → updates on `timer_tick`
  2. T2 (manual): drop WS then reconnect → poll fallback within 5s; resyncs
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
  Legacy timer thresholds are `< 600s` critical, `< 1800s` warning (`app.js`).
- Do not self-certify; an independent verifier must sign off.
- Parallel batch: only touch `useTimer.ts`, `stores/timer.ts`, `timer.test.ts`,
  `timer.spec.ts`. Integration wiring deferred to FE-020.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/composables/useTimer.ts` (new)
  - `web/frontend/src/stores/timer.ts` (modified)
  - `web/frontend/tests/unit/timer.test.ts` (new)
  - `web/frontend/tests/e2e/timer.spec.ts` (new)

## Artifact index
- `.agents/FE-023-implementer-10/DISPATCH.md`
- `.agents/FE-023-implementer-10/progress.md`
- `.agents/FE-023-implementer-10/EVIDENCE.md`
- `.agents/FE-023-implementer-10/TESTPLAN.md`
