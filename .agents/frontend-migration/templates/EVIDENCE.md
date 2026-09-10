# EVIDENCE — <TASK-ID>

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — <agent> (<UTC>)
- Deliverable: <what changed>
- Files touched: <paths>
- Commands run + output:
  ```
  <commands and observed output>
  ```
- Screenshots: <paths or "n/a">
- Test cases executed (see TESTPLAN.md): <T1 PASS, T2 PASS, ...>
- Self-check against acceptance criteria:
  1. <criterion> — <pass/fail + note>

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
