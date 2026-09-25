# TESTPLAN — FE-023

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-023` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | integration | `bun run test tests/unit/timer.test.ts` | updates on `timer_tick` | PASS — fake WS frame applies `time_remaining_seconds`; `handleMessage` ignores non-tick frames | |
| T2 | manual | drop WS then reconnect (unit equivalent) | poll fallback within 5s; resyncs | PASS (equivalent) — fake socket close → poll at 5s; reconnect at 3s → resync tick. Browser leg DEFERRED | |

## Edge cases / additions (implementer unit tests)
- `parseTimerTick` returns `null` for non-JSON, non-`timer_tick`, and non-string frames.
- Connected socket clears the fallback poll (`fetch` not called while connected).
- Transient poll errors do not stop polling.
- Server-clock interpolation between ticks (600s → 595s after 5s wall time).
- `onExpired` fires exactly once at zero and tears the timer down.
- Threshold bands: 3600 normal, 1799/600 warning, 599/0 critical.
- Colour-only guard: style has exactly one key `color`, resolves to a
  `var(--color-*)` token, no hex / animation / shadow / pulse / glow.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commit)
- Host: Bun 1.4.x, Win32, jsdom via Vitest 3.2.7
- Browser(s): Playwright chromium — host-only, DEFERRED here

## Verdict
- Implementer: PASS (by equivalent; browser DEFERRED), 2026-09-10 09:32 UTC
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
