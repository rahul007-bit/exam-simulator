# BRIEFING — FE-013

## Mission
Deliver a reusable, admin-only `DataTable` component built on `@tanstack/vue-table`
with sorting, filtering, pagination, keyboard-accessible headers/rows, and empty /
loading states, plus a demo section in `DevUiView.vue` and unit + e2e tests.

## 🔒 Identity
- Task: FE-013
- Role: implementer
- Working directory: .agents/FE-013-implementer-8
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-012
- **Acceptance criteria:** (mirror the task entry)
  1. sort/filter/paginate working
  2. keyboard-accessible headers and rows
  3. empty/loading states
- **Test cases:** (mirror `tasks.json` → `tests`)
  1. T1 (unit): sort/filter/paginate helpers — correct ordering, filtering, page slicing
  2. T2 (e2e): click header sort; filter to empty — rows reorder; empty state shown
- **Verifier:** independent-agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Tailwind + tokens only: no raw hex, no glow/gradient, no emoji.
- Strict behavioral parity (D-007) does not apply to this new admin-only surface,
  but the design-system constraints do.
- Admin use only (not candidate).
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - web/frontend/src/components/ui/DataTable.vue
  - web/frontend/src/components/ui/index.ts
  - web/frontend/src/views/DevUiView.vue
  - web/frontend/tests/unit/datatable.test.ts
  - web/frontend/tests/e2e/datatable.spec.ts

## Artifact index
- `.agents/FE-013-implementer-8/DISPATCH.md`
- `.agents/FE-013-implementer-8/progress.md`
- `.agents/FE-013-implementer-8/EVIDENCE.md`
- `.agents/FE-013-implementer-8/TESTPLAN.md`
