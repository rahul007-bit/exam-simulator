# BRIEFING — FE-012

## Mission
Deliver reusable, token-driven UI primitives (Button, Input, Select, Badge/Chip, Card,
Modal, Spinner, SegmentedControl) built on Tailwind CSS + Headless UI, plus a dev-only
primitives gallery route so a browser can run axe and a human can tab through every state.

## 🔒 Identity
- Task: FE-012
- Role: implementer
- Working directory: .agents/FE-012-implementer-7
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-002, FE-005 (both `verified`)
- **Acceptance criteria:**
  1. all variants styled from tokens only
  2. focus-visible rings; disabled/loading states
  3. no glow/gradient; no emoji
- **Test cases:**
  1. T1 (audit): axe on primitives demo → no critical violations
  2. T2 (manual/automated): tab through every primitive → visible focus ring; disabled/loading correct
- **Verifier:** independent agent (not implementer-7)

## Key constraints
- Follow `decisions.md` — D-002 (Tailwind + Headless UI), D-003 (slate + indigo palette).
- No raw hex in `src/components` / `src/views` (`hex-audit` covers them).
- Strict behavioral parity (D-007): this task adds no candidate/admin flows.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/components/ui/**`, `web/frontend/src/views/DevUiView.vue`,
  `web/frontend/src/router/index.ts` (dev route only), `web/frontend/tests/unit/ui-primitives.test.ts`,
  `web/frontend/tests/e2e/ui-primitives.spec.ts`

## Artifact index
- `.agents/FE-012-implementer-7/DISPATCH.md`
- `.agents/FE-012-implementer-7/progress.md`
- `.agents/FE-012-implementer-7/EVIDENCE.md`
- `.agents/FE-012-implementer-7/TESTPLAN.md`
