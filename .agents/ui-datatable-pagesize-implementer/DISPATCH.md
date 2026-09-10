# DISPATCH — UI-DATATABLE-PAGESIZE

## 2026-09-10T15:33:19Z
You are assigned task **UI-DATATABLE-PAGESIZE** on branch
`feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/ui-datatable-pagesize-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Enhance the shared admin `DataTable.vue` (used by the admin Sessions table,
Infrastructure table, and the Dev UI gallery) with:
1. a rows-per-page selector next to the Previous/Next controls; and
2. a fixed/max-height scrollable body with a sticky header.

### Acceptance criteria
1. `pageSizeOptions?: number[]` (default `[10, 25, 50, 100]`) and
   `maxHeight?: string` (default `'24rem'`) props, backward compatible.
2. Footer selector uses the design-system `Select`, `data-testid="datatable-page-size"`,
   an accessible name, `setPageSize` + `setPageIndex(0)`, and emits
   `update:pageSize`.
3. Wrapper is `overflow-auto` with `max-height`; `thead` is `sticky top-0`
   over an opaque `bg-elevated`.
4. Existing tests remain green; new unit tests cover both features.

### Verification method
From `web/frontend/`:
- `bun run lint`
- `bunx vue-tsc --noEmit`
- `bun run test`

### Constraints
- One focused change; no commits/pushes.
- Design tokens only; no raw hex / glow / emoji.
- Do not edit call sites unless strictly required (defaults are used).
- Do not run `bun run build` or Playwright.
