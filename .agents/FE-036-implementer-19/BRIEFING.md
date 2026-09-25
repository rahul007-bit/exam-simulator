# BRIEFING — FE-036

## Mission
Tighten the admin reset/terminate/end dialogs' spacing and make long-running
session actions non-blocking (GCP-style) so a single in-flight action never locks
or blanks the rest of the admin sessions page.

## 🔒 Identity
- Task: FE-036
- Role: implementer
- Working directory: .agents/FE-036-implementer-19
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-031 (verified)
- **Acceptance criteria:**
  1. admin action/confirm dialogs use tighter, consistent spacing (no excessive margin/padding)
  2. starting an action shows a per-row/inline busy state but does NOT block opening or acting on other sessions
  3. the sessions table stays populated during a mutation (no full-table loading blank); only the affected row's actions are disabled
  4. results are still reported via toast and actions still go through the promise confirm dialog (no native dialogs)
- **Test cases:**
  1. T1 unit — per-row pending: `isRowPending(id)` true only for the acting row
  2. T2 e2e — slow action on row A; row B still clickable, table populated, inline busy on A
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Testing paused: run only `bunx vue-tsc --noEmit`.
- Strict file ownership; do not touch shared/config files.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/views/AdminView.vue`
  - `web/frontend/src/composables/useAdminSessions.ts`
  - `web/frontend/src/components/admin/**`
  - `web/frontend/src/components/ui/Modal.vue`
  - `web/frontend/src/components/ConfirmDialog.vue`

## Artifact index
- `.agents/FE-036-implementer-19/DISPATCH.md`
- `.agents/FE-036-implementer-19/progress.md`
- `.agents/FE-036-implementer-19/EVIDENCE.md`
