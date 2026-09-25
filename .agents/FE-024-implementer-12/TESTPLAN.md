# TESTPLAN - FE-024

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-024` -> `tests`).
T1/T2 are Playwright e2e cases; per PROTOCOL §6 the browser leg is host-only and
is **DEFERRED** locally. Equivalent Vitest + jsdom coverage is recorded below and
exercises the same state mapping / payload contract.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | open question drawer | current/flagged/score states correct | PASS by equivalent (`question-nav.test.ts`, 9 tests) — browser leg DEFERRED | |
| T2 | e2e | submit exam | scorecard totals equal `/api/action/submit` payload | PASS by equivalent (`question-scorecard.test.ts`, 6 tests) — browser leg DEFERRED | |

### Equivalent Vitest coverage

| ID | Command | Assertion |
| :--- | :--- | :--- |
| T1a | `bun run test question-nav` | `navState` precedence current > flagged > scored > pending |
| T1b | `bun run test question-nav` | drawer renders Current/Flagged/Scored/Pending states + summary |
| T1c | `bun run test question-nav` | clicking a task emits `select(task_num)` and closes |
| T2a | `bun run test question-scorecard` | `scorecardRows` preserves all payload fields + `score/max` text |
| T2b | `bun run test question-scorecard` | scorecard renders percentage, totals, PASS/FAIL and every row cell |

## Edge cases / additions
- A task that is both current and flagged resolves to `current` (legacy parity).
- Empty navigator renders the empty state; uncontrolled drawer loads `/api/questions`.
- Null/undefined scorecard result renders the empty state with zero rows.

## Environment
- Commit / build: `e0fb4a3` (working tree; not committed per protocol)
- Host: win32 dev box, Bun 1.4.x, jsdom
- Browser(s): deferred to platform host

## Verdict
- Implementer: PASS, 2026-09-10 10:48 UTC
- Verifier: pending
