# TESTPLAN - ui-datatable-search-implementer

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | audit | read `DataTable.vue` pagination footer | No visible "Rows per page" label; `Select` present with `data-testid="datatable-page-size"` and `aria-label="Rows per page"` | PASS | |
| T2 | unit | `bun run test` (`datatable.test.ts` "renders the rows-per-page selector...") | `wrapper.text()` does NOT contain "Rows per page"; control has `aria-label="Rows per page"`; options unchanged | PASS | |
| T3 | unit | `bun run test` (`datatable.test.ts` "searches a custom accessor value...") | Searching hidden `code` keeps only the matching row; displayed cell text unchanged | PASS | |
| T4 | typecheck | `bunx vue-tsc --noEmit` | No type errors | PASS | |
| T5 | lint | `bun run lint` | No lint errors | PASS | |

## Edge cases / additions
- Custom accessor returns `unknown`; the DataTable must not assume a string
  (TanStack global filter handles includesString coercion).
- Admin Session accessor interpolates `${row.name} ${row.session_id ?? ''}` so
  null session ids do not inject `undefined`/`null` into the search text.
- Search placeholder now reads "Filter by name, session ID, type, status or token".

## Environment
- Commit / build: `e0fb4a3f62a9c57eef2d318534d8c016f5e0fc6d`
- Host: Windows (win32) / branch `feature/frontend-vue-migration`
- Browser(s): n/a (browser leg DEFERRED)

## Verdict
- Implementer: PASS, 2026-09-10T15:37:32Z
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
