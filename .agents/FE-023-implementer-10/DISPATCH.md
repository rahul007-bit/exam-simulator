# DISPATCH — FE-023

## 2026-09-10 09:32 UTC
You are assigned task **FE-023** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-023-implementer-10`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`useTimer` consuming `timer_tick` + `/api/timer` fallback; warning/critical
states without pulse glow.

### Acceptance criteria
1. timer stays in sync with `server_timestamp`
2. reconnects and continues correctly
3. warning/critical styles use colour only

### Verification method
- `bun run test` (unit incl. `tests/unit/timer.test.ts` with fake WS + fake timers)
- `bunx tsc --noEmit`
- `bun run lint`
- Host-only later: `bunx playwright test tests/e2e/timer.spec.ts`

### Parallel-batch scope (STRICT)
Only create/modify:
- `web/frontend/src/composables/useTimer.ts`
- `web/frontend/src/stores/timer.ts`
- `web/frontend/tests/unit/timer.test.ts`
- `web/frontend/tests/e2e/timer.spec.ts`

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; status managed by the orchestrator.
