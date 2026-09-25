# BRIEFING - FE-024

## Mission
Deliver the candidate question navigator (drawer), the admin preset selector modal
with the full-curriculum card, and the final exam scorecard — all on the FE-012
design tokens with no raw hex, glow, or emoji.

## Identity
- Task: FE-024
- Role: implementer
- Working directory: .agents/FE-024-implementer-12
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-013 (verified)
- **Acceptance criteria:**
  1. navigator reflects flagged/current/score states
  2. scorecard matches the `/api/action/submit` payload
  3. no emoji in preset cards
- **Test cases:**
  1. T1 (e2e) open question drawer -> current/flagged/score states correct
  2. T2 (e2e) submit exam -> scorecard totals equal `/api/action/submit` payload
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Do not self-certify; an independent verifier must sign off.
- Parallel batch: only create files under `src/components/candidate/` and
  `tests/unit/question-*.test.ts`; do not run the board CLI or the build.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/components/candidate/{question,scorecard}.ts`,
  `web/frontend/src/components/candidate/{QuestionDrawer,PresetModal,ExamScorecard}.vue`,
  `web/frontend/tests/unit/question-{nav,scorecard}.test.ts`

## Artifact index
- `.agents/FE-024-implementer-12/DISPATCH.md`
- `.agents/FE-024-implementer-12/progress.md`
- `.agents/FE-024-implementer-12/EVIDENCE.md`
- `.agents/FE-024-implementer-12/TESTPLAN.md`
