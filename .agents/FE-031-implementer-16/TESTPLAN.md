# TESTPLAN — FE-031

Per-task test plan. The implementer fills in the executed results; the
independent verifier re-runs and records their own results.

Test cases are defined canonically in `tasks.json` (task FE-031 → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | Select a row, run terminate/reset/end | confirm dialog, then `POST /api/admin/sessions/{id}/{terminate,reset,end}`; toast result; list refreshed | PASS (static/type review; browser leg DEFERRED — testing paused) | |
| T2 | audit | grep built bundle for `alert(`/`confirm(` | none (no native dialogs) | PASS (source audit: no `window.confirm`/`window.alert`; only `useConfirm`) | |
| T3 | unit | `bunx tsc --noEmit` | exit 0 | PASS (exit 0) | |

## Edge cases / additions
- Invite row (`type: "invite"`, `session_id: null`): identifier falls back to
  `candidate_token`; only terminate is offered (Cancel invite).
- Archived row (`type: "archived"`): only terminate is offered (Delete record).
- Active row: terminate/reset/end all offered.
- Row with neither `session_id` nor `candidate_token`: action is blocked with a
  warning toast instead of a bad request.
- Row actions disabled while a mutation is in flight (`busy`).

## Environment
- Commit / build: working tree of `feature/frontend-vue-migration` (no commit)
- Host: Windows authoring host, Bun
- Browser(s): DEFERRED (Playwright host-only; testing paused for this batch)

## Verdict
- Implementer: PASS (type + source audit), 2026-09-10T10:57:09Z
- Verifier: pending
