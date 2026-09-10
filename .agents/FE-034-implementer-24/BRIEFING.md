# BRIEFING — FE-034

## Mission
Deliver the admin **infrastructure table**: a self-contained `DataTable` view of
fleet nodes plus Docker/Incus resources, with a confirm-gated terminate action,
so the new admin SPA reaches parity with the legacy `admin.js` infrastructure
panel.

## 🔒 Identity
- Task: FE-034
- Role: implementer
- Agent: implementer-24
- Working directory: `.agents/FE-034-implementer-24`
- Branch: `feature/frontend-vue-migration`

## Task contract
- **Depends on:** FE-013 (DataTable) — claimed via orchestrator batch.
- **Acceptance criteria:**
  1. nodes + docker + incus resources listed
  2. terminate calls `/api/admin/infrastructure/terminate`
  3. confirmation via dialog
- **Test cases:** T1 — list then terminate a test resource → row removed, endpoint hit, confirm dialog.
- **Verifier:** independent agent.

## Key constraints
- TESTING PAUSED: only `bunx vue-tsc --noEmit` may be run (no test/build/Playwright/board CLI).
- Strict file ownership: only `src/components/admin/AdminInfrastructureTable.vue`
  and `src/composables/useAdminInfrastructure.ts` were created. `AdminView.vue` and
  shared files were **not** touched; wiring is the orchestrator's job.
- Tokens only (no raw hex / glow / emoji).
- Strict parity (D-007): unchanged endpoint contracts; `{ kind, node, name }` body.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Backend: `web/server.py:1613` (GET) and `web/server.py:1652` (POST terminate)
- Legacy parity: `web/static/js/admin.js:596-701`

## Artifact index
- `.agents/FE-034-implementer-24/DISPATCH.md`
- `.agents/FE-034-implementer-24/progress.md`
- `.agents/FE-034-implementer-24/EVIDENCE.md`
- `.agents/FE-034-implementer-24/TESTPLAN.md`
