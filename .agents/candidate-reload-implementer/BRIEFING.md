# BRIEFING — candidate-reload

## Mission
Implement the currently-broken header overflow **Reload** action on the candidate
exam page so it matches legacy `reloadWorkspaceFrame` behavior: reconnect the
terminal when the terminal tab is active, otherwise force a fresh noVNC
connection.

## 🔒 Identity
- Task: candidate-reload
- Role: implementer
- Working directory: .agents/candidate-reload-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-026 (`WorkspaceTabs`, already exposes `activeTab`/`terminal`/`vnc`)
- **Acceptance criteria:**
  1. `onAction('reload')` reconnects the terminal when the active tab is `terminal`.
  2. `onAction('reload')` reloads the noVNC frame otherwise (desktop/noVNC).
  3. Missing ref/instance is a guarded no-op that never throws.
  4. `switch` structure and all other cases preserved; `new-tab` unchanged.
  5. Exposed refs typed so `vue-tsc` passes.
- **Test cases:** T1–T5 in TESTPLAN.md.
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Edit only `CandidateView.vue` (plus own test + workspace metadata); do NOT touch
  Badge/TaskPane/task.ts (concurrent agent) or `WorkspaceTabs.vue`.
- No new dependencies. Design tokens only.
- Do not self-certify; an independent verifier must sign off.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/src/views/CandidateView.vue`,
  `web/frontend/tests/unit/candidate-reload.test.ts`

## Artifact index
- `.agents/candidate-reload-implementer/DISPATCH.md`
- `.agents/candidate-reload-implementer/progress.md`
- `.agents/candidate-reload-implementer/EVIDENCE.md`
