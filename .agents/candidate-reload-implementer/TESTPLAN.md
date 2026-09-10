# TESTPLAN — candidate-reload

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `candidate-reload` →
`tests`). Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bunx vitest run tests/unit/candidate-reload.test.ts` | Reload with `activeTab === 'terminal'` calls `terminal.reconnect()` once, not `vnc.reload()` | PASS | |
| T2 | unit | same | Reload with `activeTab === 'desktop'` calls `vnc.reload()` once, not `terminal.reconnect()` | PASS | |
| T3 | unit | same | Reload when the workspace is unmounted (no ref) resolves without throwing and calls neither handle | PASS | |
| T4 | typecheck | `bunx vue-tsc --noEmit` | Exposed refs typed; no TS errors | PASS | |
| T5 | lint | `bun run lint` | No ESLint errors in workspace | PASS | |

## Edge cases / additions
- Guard against `workspaceTabs.value` being `null` (workspace rendered only when
  a session is active) — covered by T3.
- Optional chaining on `terminal`/`vnc` handles is defensive; the stubbed
  island always exposes both.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commit)
- Host: win32, pwsh, Bun + vitest 3.2.7, vue-tsc 2.x
- Browser(s): n/a (jsdom)

## Verdict
- Implementer: PASS, 2026-09-10 15:51 UTC
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
