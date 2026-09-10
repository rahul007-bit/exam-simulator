# TESTPLAN — FE-020

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-020` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | load candidate view | header shows name/progress/timer/Flag/Submit; secondary in overflow | DEFERRED (browser is host-only; batch is typecheck-only) | |
| T2 | audit | screenshot at 1366x768 and 1920x1080 | no overflow/clipping | DEFERRED (browser is host-only) | |
| T3 | audit | `bunx tsc --noEmit` | exit 0 | PASS (`EXIT=0`) | |
| T4 | audit | grep for raw hex / glow in new files | 0 matches | PASS | |

## Edge cases / additions
- Long exam name: must truncate (`truncate min-w-0`) instead of pushing the
  primary controls off-screen.
- No active session: Flag/Submit/progress hidden; overflow still available.
- Admin: End/Reset appear in the overflow; candidate does not see them.
- `Copy session ID` disabled until a session id exists.
- Timer urgency is colour-only (no pulse/glow) via FE-023 tokens.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commit)
- Host: local Windows authoring host (Bun); canonical host is the platform host
- Browser(s): n/a locally (Playwright DEFERRED)

## Verdict
- Implementer: PASS (typecheck), browser e2e/audit DEFERRED, 2026-09-10 11:01 UTC
- Verifier: <pending>
