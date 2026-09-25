# TESTPLAN — FE-013

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results.

Test cases are defined canonically in `tasks.json` (task `FE-013` → `tests`).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run test` (`tests/unit/datatable.test.ts`) | correct ordering, filtering, page slicing | PASS — 8/8 cases | |
| T2 | e2e | `bunx playwright test tests/e2e/datatable.spec.ts` (host) | rows reorder on header sort; empty state after filtering to no match | DEFERRED (browser leg, PROTOCOL §6) — equivalent jsdom coverage in T1 PASS | |

## Edge cases / additions
Implemented as additional Vitest cases in `tests/unit/datatable.test.ts`:

1. renders one header per column and the page's rows;
2. ascending then descending sort from the header button updates order and
   `aria-sort`;
3. global filter narrows rows and reports the filtered count;
4. filtering to no match renders `[data-testid="datatable-empty"]`;
5. `pageSize` slices rows; next/previous navigate and the page indicator updates;
6. `loading` renders an `aria-busy` table with a labelled Spinner and no rows;
7. sortable headers are `<button>`s; `interactive` rows are focusable
   (`tabindex="0"`) and Enter emits `row-click`;
8. custom cell renderer output and right-aligned columns.

Authored (not executed locally) e2e cases in `tests/e2e/datatable.spec.ts`:
header-sort + `aria-sort`, filter-to-empty, keyboard sort, pagination +
focusable rows. The orchestrator runs Playwright on the host.

## Environment
- Commit / build: unbaked working tree on `feature/frontend-vue-migration`
- Host: Windows workstation (bun 1.4.x), Vitest + jsdom
- Browser(s): Playwright chromium on the platform host — DEFERRED to orchestrator

## Raw acceptance output
```
bun run test      -> Test Files 12 passed (12); Tests 138 passed (138)
bunx tsc --noEmit -> exit 0
bunx vue-tsc --noEmit -> exit 0
bun run lint      -> exit 0
```

## Verdict
- Implementer: PASS (2026-09-10T09:30:27Z), Playwright leg DEFERRED
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
