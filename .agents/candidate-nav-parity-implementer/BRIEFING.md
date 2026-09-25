# BRIEFING - candidate-nav-parity

## Mission
Restore strict legacy parity (D-007) on the candidate page: add the missing
task footer (Previous · Reset task · Task X of Y · Next) and make the question
navigator re-fetch `/api/questions` on every open so a task jump is reflected.

## Identity
- Task: candidate-nav-parity
- Role: implementer
- Working directory: `.agents/candidate-nav-parity-implementer`
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** none
- **Acceptance criteria:**
  1. `TaskPane.vue` renders a footer with Previous / Reset task / Task X of Y /
     Next, disabled at first/last task and while busy; emits `prev`/`next`/`reset`.
  2. `CandidateView.vue` wires the footer to `session.prev()/next()/retry()` with
     confirm + toasts; non-blocking.
  3. `QuestionDrawer.vue` reloads on every uncontrolled open (no stale cache);
     controlled mode unchanged.
  4. Unit + E2E coverage; lint, typecheck, vitest, playwright all green.
- **Test cases:** see `TESTPLAN.md`.
- **Verifier:** independent agent

## Key constraints
- Strict behavioural parity (D-007); reuse design tokens only (no raw hex/emoji).
- Do not touch `web/server.py`, `web/static`, `docker/**`, fonts, styles, other
  tests, or board files. Do not commit/push. Orchestrator rebuilds/redeploys.

## Pointers
- Workspace brief: `.agents/candidate-nav-parity-implementer/DISPATCH.md`
- Evidence: `.agents/candidate-nav-parity-implementer/EVIDENCE.md`
- Tests: `.agents/candidate-nav-parity-implementer/TESTPLAN.md`

## Artifact index
- `.agents/candidate-nav-parity-implementer/DISPATCH.md`
- `.agents/candidate-nav-parity-implementer/progress.md`
- `.agents/candidate-nav-parity-implementer/EVIDENCE.md`
- `.agents/candidate-nav-parity-implementer/TESTPLAN.md`
