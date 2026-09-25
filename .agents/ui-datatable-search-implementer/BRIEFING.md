# BRIEFING - ui-datatable-search-implementer

## Mission
Remove the visible "Rows per page" text from `DataTable` pagination (keeping the
selector, now with a non-visual accessible name) and make the admin Sessions
table global search also match the session ID via an optional column-level
`accessor`, without adding a visible column.

## Identity
- Task: ui-datatable-search-implementer
- Role: implementer
- Working directory: `.agents/ui-datatable-search-implementer`
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** none
- **Acceptance criteria:**
  1. `DataTable.vue` no longer renders the visible "Rows per page" label/text;
     the page-size `Select` remains (`data-testid="datatable-page-size"`,
     functional) and carries `aria-label="Rows per page"` (+ optional `title`).
  2. `DataTableColumn<T>` exposes optional `accessor?: (row: T) => unknown`;
     `DataTable.vue` builds accessors through it when provided. Admin Sessions
     "Session" column uses it so search matches name + `session_id`; the cell
     still shows only the name; search placeholder mentions session ID; no
     visible column change.
  3. Unit tests updated (`datatable.test.ts`): the "Rows per page" text
     assertion is replaced by an accessible-name check and a new test proves a
     custom `accessor` value is searchable; all existing tests still pass.
- **Test cases:** (see TESTPLAN.md) T1-T5.
- **Verifier:** independent agent

## Key constraints
- Do NOT commit/amend/push; do NOT run `scripts/agents_board.py`.
- Do NOT run `bun run build` or Playwright.
- Only run `bun run lint`, `bunx vue-tsc --noEmit`, `bun run test` from
  `web/frontend/`.
- Use design tokens only - no raw hex, no emoji/glow.
- Do not touch shared files outside the owned set.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/components/ui/DataTable.vue`,
  `web/frontend/src/components/ui/index.ts`,
  `web/frontend/src/views/AdminView.vue`,
  `web/frontend/tests/unit/datatable.test.ts`,
  `.agents/ui-datatable-search-implementer/*`

## Artifact index
- `.agents/ui-datatable-search-implementer/DISPATCH.md`
- `.agents/ui-datatable-search-implementer/progress.md`
- `.agents/ui-datatable-search-implementer/EVIDENCE.md`
- `.agents/ui-datatable-search-implementer/TESTPLAN.md`
