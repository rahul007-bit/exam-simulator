# TESTPLAN — FE-036

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-036` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `isRowPending(id)` true only for the acting row; `isPending(id, action)` true only for the matching action | other identifiers report not pending | PASS (logic/audit; test runner paused) | |
| T2 | e2e | trigger a slow action on row A; confirm row B is still clickable and the table stays populated | no global block; inline busy on row A | DEFERRED (browser host-only; testing paused) | |
| A1 | audit | `bunx vue-tsc --noEmit` | exit 0 | PASS | |
| A2 | audit | grep owned files for native dialogs (`window.confirm`/`alert`) | none | PASS | |
| A3 | auth | `runAction` calls `fetchSessions({ silent: true })`; DataTable `:loading="loading"` (initial only) | no global blank | PASS (static) | |

## Edge cases / additions
- Opening the same row that is already pending: dialog shows the pending action
  with a spinner and disables that row's action buttons; Close stays enabled.
- Opening a *different* row while one action is in flight: all of that other
  row's action buttons remain enabled.
- Refresh during an in-flight mutation: Refresh stays enabled (it is disabled
  only while its own `fetchSessions` runs, i.e. `refreshing || loading`).
- Action success still toasts; failure still toasts; both flow through
  `useConfirm`. No native dialogs introduced.

## Environment
- Commit / build: `feature/frontend-vue-migration` working tree (web/frontend/ untracked)
- Host: local Windows dev box
- Browser(s): n/a locally — browser leg DEFERRED

## Verdict
- Implementer: PASS (with T2 DEFERRED), 2026-09-10T11:12:29Z
- Verifier: pending
