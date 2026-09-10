# EVIDENCE — UI-DATATABLE-PAGESIZE

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-datatable-pagesize (2026-09-10T15:33:19Z)
- Deliverable: shared admin `DataTable` now renders a rows-per-page `Select`
  next to Previous/Next, and its body scrolls within a max height with a sticky,
  opaque header.
- New props / defaults:
  - `pageSizeOptions?: number[]` — default `[10, 25, 50, 100]`
  - `maxHeight?: string` — default `'24rem'`
  - On change: `table.setPageSize(n)` **and** `table.setPageIndex(0)`, then
    `emit('update:pageSize', n)`.
- Files touched:
  - `web/frontend/src/components/ui/DataTable.vue` (modified)
  - `web/frontend/tests/unit/datatable.test.ts` (modified; +4 cases, 8 existing
    unchanged)
  - `.agents/ui-datatable-pagesize-implementer/{BRIEFING,DISPATCH,progress,EVIDENCE,TESTPLAN}.md`
- Call sites left untouched: `src/views/AdminView.vue`,
  `src/components/admin/AdminInfrastructureTable.vue`, `src/views/DevUiView.vue`
  (defaults provide the new behavior).
- Screenshots: n/a

### Commands run + output

```
$ bun run lint
$ eslint .
LINT_EXIT=0

$ bunx vue-tsc --noEmit
VUETSC_EXIT=0

$ bun run test
 Test Files  17 passed (17)
      Tests  193 passed (193)   # baseline 189 + 4 new
   tests/unit/datatable.test.ts (12 tests) passed

$ bunx vitest run tests/unit/datatable.test.ts
 Tests  12 passed (12)
```

- Test cases executed (see TESTPLAN.md): T1 PASS, T2 PASS, T3 PASS, T4 PASS.

### Self-check against acceptance criteria
1. Backward-compatible props — PASS. `pageSizeOptions` / `maxHeight` are optional
   with defaults; every existing prop and behavior is unchanged.
2. Rows-per-page selector — PASS. Footer renders a `Select` labelled
   "Rows per page" with `data-testid="datatable-page-size"`; options are
   de-duplicated/sorted and always include the current `pageSize`. Selection
   calls `setPageSize` + `setPageIndex(0)` and emits `update:pageSize`
   (asserted with `pageSize: 2` → `'25'` → 5 rows, "Page 1 of 1",
   `update:pageSize` = `[25]`).
3. Scroll + sticky header — PASS. Wrapper is `overflow-auto` with
   `style="max-height: <maxHeight>"`; `thead` has `sticky top-0 z-10
   bg-elevated` (opaque token `--color-elevated`).
4. No regressions — PASS. Original 8 FE-013 cases unchanged and green; full
   suite 193/193; token audits (`hex-audit`, `decor-audit`,
   `ui-primitives` audited block) pass.

### Notes / deviations
- None. No shared config or file outside the declared scope was modified.

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
