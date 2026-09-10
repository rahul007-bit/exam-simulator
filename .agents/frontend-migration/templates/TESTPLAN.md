# TESTPLAN — <TASK-ID>

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `<TASK-ID>` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit/integration/e2e/manual/audit | `<command or action>` | `<observable outcome>` | PASS/FAIL + note | PASS/FAIL + note |

## Edge cases / additions
- ...

## Environment
- Commit / build: <hash>
- Host: <platform host / branch>
- Browser(s): <if applicable>

## Verdict
- Implementer: <PASS/FAIL, timestamp>
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
