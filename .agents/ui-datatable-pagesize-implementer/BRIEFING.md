# BRIEFING — UI-DATATABLE-PAGESIZE

## Mission
Enhance the shared admin `DataTable` with a rows-per-page selector and a
fixed/max-height scrollable body whose header stays sticky, without breaking any
existing consumer or test.

## 🔒 Identity
- Task: UI-DATATABLE-PAGESIZE
- Role: implementer
- Working directory: .agents/ui-datatable-pagesize-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-013 (DataTable), FE-012 (Select primitive)
- **Acceptance criteria:**
  1. `DataTable` exposes `pageSizeOptions` (default `[10, 25, 50, 100]`) and
     `maxHeight` (default `'24rem'`) props, backward compatible.
  2. Pagination footer renders a visible "Rows per page" `Select` with
     `data-testid="datatable-page-size"` and an accessible name; changing it
     calls `setPageSize` + `setPageIndex(0)` and emits `update:pageSize`.
  3. Table wrapper scrolls internally with `maxHeight`; `thead` is sticky and
     opaque.
  4. Existing FE-013 behavior/tests stay green; new unit tests cover the
     selector and sticky/scroll container.
- **Test cases:** `bun run lint`, `bunx vue-tsc --noEmit`, `bun run test`
- **Verifier:** independent agent

## Key constraints
- Design tokens only — no raw hex, no glow/gradient/emoji (`hex-audit`,
  `decor-audit`).
- Do NOT commit/push; do NOT run `bun run build` or Playwright.
- Do not touch files outside `web/frontend/src/components/ui/DataTable.vue` and
  `web/frontend/tests/unit/datatable.test.ts` (call sites rely on defaults).

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/components/ui/DataTable.vue`,
  `web/frontend/tests/unit/datatable.test.ts`

## Artifact index
- `.agents/ui-datatable-pagesize-implementer/DISPATCH.md`
- `.agents/ui-datatable-pagesize-implementer/progress.md`
- `.agents/ui-datatable-pagesize-implementer/EVIDENCE.md`
- `.agents/ui-datatable-pagesize-implementer/TESTPLAN.md`
