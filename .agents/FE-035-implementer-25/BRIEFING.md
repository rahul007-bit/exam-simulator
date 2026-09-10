# BRIEFING — FE-035

## Mission
Deliver the admin live "observe" surface: a full-screen overlay that attaches to a
single explicit session (view-only desktop + terminal) and exposes reset/end admin
actions, without any possibility of cross-session attach.

## 🔒 Identity
- Task: FE-035
- Role: implementer
- Working directory: .agents/FE-035-implementer-25
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-025 (XTerm island), FE-026 (noVNC island)
- **Acceptance criteria:** (mirror the task entry)
  1. observe connects to the selected session only
  2. admin reset/end available in observe
  3. no cross-session leakage
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 (e2e): observe active session → terminal/desktop attach; reset/end work
  2. T2 (integration): attempt cross-session attach → rejected (server close 1008)
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS + URL/token contracts.
- File ownership: only `components/admin/ObserveOverlay.vue` and
  `composables/useObserve.ts` (plus this workspace) may be created/modified.
- Do not touch `AdminView.vue`; report integration wiring instead.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/composables/useObserve.ts`,
  `web/frontend/src/components/admin/ObserveOverlay.vue`

## Artifact index
- `.agents/FE-035-implementer-25/DISPATCH.md`
- `.agents/FE-035-implementer-25/progress.md`
- `.agents/FE-035-implementer-25/EVIDENCE.md`
- `.agents/FE-035-implementer-25/TESTPLAN.md`
