# TESTPLAN — UI-DATATABLE-PAGESIZE

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run test` (`tests/unit/datatable.test.ts`) | selector defaults + resizing + sticky/scroll assertions pass; original 8 cases unchanged | PASS — 12/12 in file | |
| T2 | lint | `bun run lint` | no ESLint errors | PASS — exit 0 | |
| T3 | types | `bunx vue-tsc --noEmit` | no type errors | PASS — exit 0 | |
| T4 | unit (suite) | `bun run test` | all pre-existing tests still pass | PASS — 17 files / 193 tests | |

## Edge cases / additions
- Default page-size options include `props.pageSize` even when it is not part of
  the supplied `pageSizeOptions` list (control always shows the current size).
- Options are de-duplicated and sorted ascending.
- Page index resets to 0 when the page size grows so the view never lands on an
  out-of-range page.
- `maxHeight` default `'24rem'` and header sticky are asserted directly on the
  rendered DOM.

## Environment
- Commit / build: unbaked working tree on `feature/frontend-vue-migration`
- Host: Windows workstation (bun 1.4.x), Vitest + jsdom
- Browser(s): n/a (Playwright not run per dispatch)

## Raw acceptance output
```
bun run test          -> Test Files 17 passed (17); Tests 193 passed (193)
bun run lint          -> exit 0
bunx vue-tsc --noEmit -> exit 0
```

## Verdict
- Implementer: PASS (2026-09-10T15:33:19Z)
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
