# DISPATCH — FE-034

## 2026-09-10 11:27 UTC
You are assigned task **FE-034** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-034-implementer-24`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Admin infrastructure table: `useAdminInfrastructure` composable + self-contained
`AdminInfrastructureTable.vue` (nodes + Docker/Incus resources, resource summary,
confirm-gated terminate).

### Acceptance criteria
1. nodes + docker + incus resources listed
2. terminate calls `/api/admin/infrastructure/terminate` with `{ kind, node, name }`
3. confirmation via the promise `useConfirm` dialog; result reported via `useToast`

### Verification method
- `bunx vue-tsc --noEmit` (EXIT 0).
- Manual (host-only, deferred): open admin page, confirm nodes/resources render,
  click Terminate on a test resource, confirm dialog appears, row disappears after OK.
- TESTING PAUSED — no `bun run test` / `bun run build` / Playwright.

### Constraints
- One focused change; only the two owned files.
- Preserve parity behavior (endpoint + payload unchanged).
- Do not edit `AdminView.vue`; report wiring notes for the orchestrator.
