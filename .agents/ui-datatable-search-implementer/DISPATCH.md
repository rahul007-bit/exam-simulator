# DISPATCH - ui-datatable-search-implementer

## 2026-09-10T15:37:32Z
You are assigned task **ui-datatable-search-implementer** on branch
`feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/ui-datatable-search-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
1. `DataTable.vue`: remove the visible "Rows per page" label, keep the page-size
   `Select` and give it `aria-label="Rows per page"` (+ `title`).
2. `index.ts`: add optional `accessor?: (row: T) => unknown` to
   `DataTableColumn<T>`; `DataTable.vue` honors it for sorting/global filtering
   while `cell` still controls display.
3. `AdminView.vue`: Sessions "Session" column accessor includes `session_id`;
   cell still shows only `name`; placeholder updated to mention session ID.
4. `datatable.test.ts`: replace the visible-text assertion with an
   accessible-name check; add a custom-accessor search test.

### Acceptance criteria
1. No visible "Rows per page" text; selector present, functional, labelled.
2. Custom accessor drives global search; Session column matches session ID with
   no new visible column; placeholder mentions session ID.
3. `bun run lint`, `bunx vue-tsc --noEmit`, `bun run test` all pass; test count
   reported.

### Verification method
From `web/frontend/`:
- `bun run lint`
- `bunx vue-tsc --noEmit`
- `bun run test`

### Constraints
- One focused change set.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Do NOT commit/push; browser leg deferred.
- Update `EVIDENCE.md` with proof.
