# BRIEFING — FE-031

## Mission
Deliver the admin sessions/invitations/history table and its terminate/reset/end
row actions, using the shared `DataTable` and the dialog/toast services (no native
dialogs), so M4 has its core session-management surface.

## 🔒 Identity
- Task: FE-031
- Role: implementer (`implementer-16`)
- Working directory: `.agents/FE-031-implementer-16`
- Branch: `feature/frontend-vue-migration`

## Task contract
- **Depends on:** FE-013 (DataTable), FE-011 (useConfirm)
- **Acceptance criteria:**
  1. table sorting/filtering/pagination via `DataTable`
  2. actions call the correct admin endpoints
  3. no native `confirm()`/`alert()`
- **Test cases (tasks.json):**
  1. T1 (e2e): terminate/reset/end from table → confirm dialog then correct endpoint hit
  2. T2 (audit): grep built bundle for `alert(`/`confirm(` → none
- **Verifier:** independent agent

## Key constraints
- Strict file ownership: only `views/AdminView.vue`, `components/admin/**`,
  `composables/useAdminSessions.ts`.
- Testing paused: run only `bunx tsc --noEmit`.
- Parity (D-007): action availability per row type mirrors legacy `admin.js`.
- Tailwind + tokens only; no raw hex/glow/emoji.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/views/AdminView.vue`,
  `web/frontend/src/components/admin/SessionActionsDialog.vue`,
  `web/frontend/src/composables/useAdminSessions.ts`

## Artifact index
- `.agents/FE-031-implementer-16/DISPATCH.md`
- `.agents/FE-031-implementer-16/progress.md`
- `.agents/FE-031-implementer-16/EVIDENCE.md`
- `.agents/FE-031-implementer-16/TESTPLAN.md`
