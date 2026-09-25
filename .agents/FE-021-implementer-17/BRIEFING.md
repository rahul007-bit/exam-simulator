# BRIEFING — FE-021

## Mission
Prioritize the candidate desktop/terminal workspace: a persisted, draggable
split-pane (default 24% / 76%, min `[300, 520]px`) with double-click reset and a
collapse-left toggle — no new dependencies.

## 🔒 Identity
- Task: FE-021
- Role: implementer
- Working directory: .agents/FE-021-implementer-17
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-020 (verified)
- **Acceptance criteria:**
  1. Right pane gets >=76% by default.
  2. Split ratio persists across reloads.
  3. Collapse toggle maximizes the workspace.
- **Test cases:** (mirror `tasks.json` → `tests`; record results in TESTPLAN.md)
  1. T1 — load workspace → right pane >=76% width.
  2. T2 — drag gutter then reload → ratio persisted in `localStorage`.
  3. T3 — toggle collapse-left → left hidden, workspace full width.
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Do not self-certify; an independent verifier must sign off.
- No new dependencies; CSS flex + pointer events only.
- FE-026 owns the Desktop/Terminal tab bar — leave `TODO(workspace-tabs)`, do not import `NoVncFrame.vue`.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md` (§5 candidate UX)
- Protocol: `.agents/frontend-migration/PROTOCOL.md` (§9 batch rules)
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/components/layout/**`,
  `web/frontend/src/views/CandidateView.vue`,
  `web/frontend/src/composables/useSplitPane.ts`

## Artifact index
- `.agents/FE-021-implementer-17/DISPATCH.md`
- `.agents/FE-021-implementer-17/progress.md`
- `.agents/FE-021-implementer-17/EVIDENCE.md`
- `.agents/FE-021-implementer-17/TESTPLAN.md`
