# EVIDENCE — FE-013

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-8 (2026-09-10T09:30:27Z)
- Deliverable: reusable admin `DataTable` on `@tanstack/vue-table@9.2.4`
  (v9 `useTable` + `tableFeatures`), with:
  - sorting (single-column, asc↔desc toggle; no removal cycle),
  - global filtering (search box over `filterFn_includesString`),
  - client pagination (page size prop, prev/next, page indicator),
  - keyboard-accessible headers (real `<button>` in `th[scope=col]` with
    `aria-sort`) and focusable/activatable rows when `interactive`,
  - empty and loading states (`datatable-empty`, announced `role="status"` +
    `aria-busy`).
- Files touched:
  - `web/frontend/src/components/ui/DataTable.vue` (new)
  - `web/frontend/src/components/ui/index.ts` (barrel + `DataTableColumn` type)
  - `web/frontend/src/views/DevUiView.vue` (demo section, 12 sample sessions)
  - `web/frontend/tests/unit/datatable.test.ts` (new, 8 cases)
  - `web/frontend/tests/e2e/datatable.spec.ts` (new, 4 cases)
- Screenshots: n/a (browser leg DEFERRED to the orchestrator/host)

### Commands run + output

```
$ bun run test
 Test Files  12 passed (12)
      Tests  138 passed (138)
   tests/unit/datatable.test.ts (8 tests) passed

$ bunx tsc --noEmit
TSC_EXIT=0

$ bunx vue-tsc --noEmit
VUETSC_EXIT=0

$ bun run lint
LINT_EXIT=0
```

The raw-hex audit (`tests/unit/hex-audit.test.ts`) and the FE-012
hex/glow/emoji audit (`tests/unit/ui-primitives.test.ts`, which also scans
`src/components/ui` and `src/views/DevUiView.vue`) both pass with the new files.

- Test cases executed (see TESTPLAN.md):
  - T1 (unit, sort/filter/paginate) — PASS (8/8 cases).
  - T2 (e2e, header sort + empty state) — browser leg DEFERRED to the
    orchestrator; equivalent jsdom coverage in T1 (sort reorder, filter to
    empty) PASS.
- Self-check against acceptance criteria:
  1. sort/filter/paginate working — PASS. `tests/unit/datatable.test.ts`
     drives the real rendered controls: header clicks reorder rows and toggle
     `aria-sort`; the search box narrows rows and resets to page 1; `pageSize`
     slices rows and next/previous navigate.
  2. keyboard-accessible headers and rows — PASS. Sort headers are
     `<button type="button">` elements inside `th[scope="col"]` with `aria-sort`;
     `interactive` rows get `tabindex="0"` and respond to Enter/Space
     (`row-click`). The e2e spec sorts from the keyboard.
  3. empty/loading states — PASS. Filtering to no match renders
     `[data-testid="datatable-empty"]`; `loading` renders an `aria-busy` table
     with a labelled Spinner and no rows.

### Notes / deviations
- `@tanstack/vue-table` here is **v9.2.4**, whose API differs from v8: there is
  no `getCoreRowModel()`; row models are feature slots on `tableFeatures` and
  state is read through `table.atoms.<slice>.get()`. The wrapper targets v9.
- The SFC is generic (`generic="T extends object"`); internally it uses a
  `Record<string, unknown>` table type and casts at the boundary because the
  v9 `ColumnDef` value type is invariant. The public prop/cell types remain
  `T`-typed for callers.
- The e2e spec (`tests/e2e/datatable.spec.ts`) was authored but not executed
  locally (Playwright is host-only per PROTOCOL §6); the orchestrator runs it.

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
