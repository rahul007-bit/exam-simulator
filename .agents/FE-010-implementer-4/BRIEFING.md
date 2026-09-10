# BRIEFING — FE-010

## Mission
Deliver the toast service (`useToast()`) and the single app-level `<Toaster/>`
component that renders info/success/warning/error notifications with stacking,
auto-dismiss, manual dismiss and an `aria-live` region — replacing native dialogs
as part of the M2 UI system.

## 🔒 Identity
- Task: FE-010
- Role: implementer
- Working directory: .agents/FE-010-implementer-4
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-002 (verified)
- **Acceptance criteria:** (mirror the task entry)
  1. four variants with semantic colors
  2. stacking + auto-dismiss + manual dismiss
  3. aria-live announced; keyboard dismissible
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 (unit) `toast.push each variant` → 4 variants render, stack, auto-dismiss
  2. T2 (audit) `axe on toaster` → aria-live present, no critical
- **Verifier:** independent agent (not implementer-4)

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007) does not affect this UI-only task.
- D-003/FE-014: use `tokens.css` only, prefer `--color-*-text` variants; no raw hex,
  no glow, no emoji.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/composables/useToast.ts` (new)
  - `web/frontend/src/components/Toaster.vue` (new)
  - `web/frontend/src/App.vue` (mount once)
  - `web/frontend/tests/unit/toast.test.ts` (new)
  - `web/frontend/eslint.config.js` (allow the documented `Toaster` name)

## Artifact index
- `.agents/FE-010-implementer-4/DISPATCH.md`
- `.agents/FE-010-implementer-4/progress.md`
- `.agents/FE-010-implementer-4/EVIDENCE.md`
- `.agents/FE-010-implementer-4/TESTPLAN.md`
