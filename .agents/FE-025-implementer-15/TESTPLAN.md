# TESTPLAN — FE-025

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-025` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | integration | run `echo hi` in terminal | output returned over `/ws/terminal/<sid>` | BLOCKED — needs `@xterm/*` installed + running backend | — |
| T2 | manual | resize then reconnect | fits container; buffer replayed | BLOCKED — needs `@xterm/*` installed + running backend | — |
| T3 | audit | `bunx tsc --noEmit` (cwd `web/frontend`) | exit 0 | PASS (exit 0) — note: plain `tsc` skips `.vue` | — |
| T4 | audit | scan the two files for raw hex / glow / emoji | none | PASS — colours read from `--color-*` tokens; no literals | — |

## Edge cases / additions
- Candidate session with an empty `sessionId` must not throw: URL degrades to
  `/ws/terminal` (server rejects non-admin explicit-less attaches with close 1008).
- Reconnect must not stack `onData`/`onResize` listeners: handlers are disposed on
  every `disconnect()` and re-bound on `open`.
- Zero-size / hidden container: `fit()` is wrapped in a try/catch.
- Server already replays Redis scrollback on connect; `replayScrollback()` is an
  explicit fallback and is **not** auto-invoked on `open` to avoid double writes.

## Environment
- Commit / build: working tree, no commit (batch rules)
- Host: Windows dev box (win32), Bun 1.4.x, `bunx tsc`
- Browser(s): n/a for T3/T4; T1/T2 require the platform host + Chrome

## Verdict
- Implementer: BLOCKED on missing `@xterm/xterm` + `@xterm/addon-fit`; `tsc` PASS.
- Verifier: <pending>
