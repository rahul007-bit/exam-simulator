# BRIEFING — FE-032

## Mission
Add the admin configuration plane: a default-preset selector and a server
resource-limit form, both wired to the existing typed admin endpoints with
inline validation and toast feedback.

## 🔒 Identity
- Task: FE-032
- Role: implementer
- Working directory: .agents/FE-032-implementer-22
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-012
- **Acceptance criteria:** (mirror the task entry)
  1. Forms reflect `/api/admin/config` and `/api/admin/resources`.
  2. Validation errors shown via toast/inline.
  3. Success feedback via toast.
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 (e2e) set default preset, reload -> value persists from `/api/admin/config`.
  2. T2 (e2e) submit invalid max sessions -> inline/toast error, no save.
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Do not self-certify; an independent verifier must sign off.
- Batch rules: disjoint file ownership; testing paused (only `bunx vue-tsc --noEmit`).

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/views/AdminView.vue`
  - `web/frontend/src/components/admin/AdminConfigForm.vue` (new)
  - `web/frontend/src/components/admin/AdminResourceForm.vue` (new)
  - `web/frontend/src/composables/useAdminConfig.ts` (new)

## Artifact index
- `.agents/FE-032-implementer-22/DISPATCH.md`
- `.agents/FE-032-implementer-22/progress.md`
- `.agents/FE-032-implementer-22/EVIDENCE.md`
- `.agents/FE-032-implementer-22/TESTPLAN.md`
