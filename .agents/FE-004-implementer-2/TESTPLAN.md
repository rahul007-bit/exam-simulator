# TESTPLAN — FE-004

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-004` → `tests`).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `npm run gen:api && npx tsc --noEmit` (accepted local: `bun run gen:api && bunx tsc --noEmit`) | types generate; exit 0 | **PASS** — `bun run gen:api` wrote `src/api/schema.d.ts` (30,268 B); `bun run typecheck` (vue-tsc) exit 0; `node node_modules/typescript/bin/tsc --noEmit` exit 0. `npx tsc`/`bunx tsc` unavailable (Bun-installed `.bin`, offline) — see NOTES. | **PASS** (verifier-3) — `bun run gen:api` exit 0, wrote `schema.d.ts`; `bun run typecheck` exit 0; `bunx tsc --noEmit` (local TS 5.7.3) exit 0. `npx tsc` binary leg not needed. |
| T2 | integration | session store `fetchSession()` | typed `/api/session` data populated | **PASS** — `tests/unit/stores.test.ts` mocks `fetch` and asserts `isActive`, `sessionId`, `currentTask.id`, `totalTasks`, `currentTaskNum`; plus timer/presets/action/error cases. 10 tests pass offline. | **PASS** (verifier-3) — 10/10 store tests pass; `fetchSession()` populates typed state from mocked `/api/session`, query-param + `ApiError` handling verified. Live-backend leg **DEFERRED** (Linux-only backend / host unreachable). | |

## Edge cases / additions (implementer)
- **Query params** — `fetchSession({ token, admin })` builds
  `/api/session?admin=true&token=tok-1`.
- **Error handling** — HTTP 400 `{detail}` surfaces as `ApiError` message; store
  `error` set and `fetchSession()` returns `null` (no throw).
- **Session union** — `active: true | false` discriminated; `invited` variant handled by
  `isInvited`; `locked_preset` exposed for inactive/invited.
- **Actions** — `flag()` updates `flagged_ids` in place; `submit()` returns the typed
  scorecard report and clears the session; `next/prev/jump/retry` typed.
- **Timer** — `syncFromSession()` seeds from `/api/session`; `applyTick()` consumes the
  `timer_tick` WS payload; `formatted`/`urgency`/`isExpired` computed.
- **Presets** — catalog + `selected` from `/api/presets`; `selectPreset()` POST body
  `{"preset": ...}`.
- **Regression commands** — `bun run lint` exit 0; `bun run build` exit 0; `bun run
  format:check` clean; full `bun run test` 6 files / 48 tests pass.

## Environment
- Branch / commit: `feature/frontend-vue-migration` @ `e0fb4a3`
- Host: Windows workstation; **Bun 1.4.2**; Node v26.8.2 present; Python 3.12.4
- Backend: FastAPI is Linux-only and cannot run locally; `10.8.0.15:3000` answers TCP
  + HTTP 200 but stalls before the response body → live API checks are host-only.

## Verdict
- Implementer: PASS (2026-09-10T07:26:19Z), with the live-`openapi.json` generation leg
  **DEFERRED** (host body stall) and the literal `npx tsc` binary leg run via accepted
  Bun equivalents.
- Verifier: **REJECTED** (verifier-3, 2026-09-10T07:33:53Z). T1/T2 PASS and no
  regression, but `openapi.json` fidelity fails on `GET /api/admin/sessions`
  (`AdminSessionItem` omits `container_running`/`current_index`/`type`/`url`, adds a
  never-returned `time_limit_minutes`, and `total_tasks` is non-null though invite
  rows return `null`). All other covered endpoints match `web/server.py`.
  Host-only legs: live `/openapi.json` diff and live `/api/session` — DEFERRED.
