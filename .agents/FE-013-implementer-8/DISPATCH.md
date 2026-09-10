# DISPATCH — FE-013

## 2026-09-10T09:30:27Z
You are assigned task **FE-013** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-013-implementer-8`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Reusable DataTable component (sorting, filtering, pagination) built on
`@tanstack/vue-table`, admin use only. Includes a DataTable demo section in
`DevUiView.vue`, unit tests, and an e2e spec.

### Acceptance criteria
1. sort/filter/paginate working
2. keyboard-accessible headers and rows
3. empty/loading states

### Verification method
- `bun run test` (unit suite includes `tests/unit/datatable.test.ts`)
- `bunx tsc --noEmit` (and `bunx vue-tsc --noEmit`) and `bun run lint`
- Playwright `tests/e2e/datatable.spec.ts` run by the orchestrator on the host

### Constraints
- One focused change; only touch the five owned files.
- Tailwind + tokens only: no raw hex, no glow/gradient, no emoji.
- Preserve parity behavior (WS, clipboard, timer, token routing) — untouched here.
- Update `EVIDENCE.md` with proof; do not run the board CLI (orchestrator owns tasks.json).
