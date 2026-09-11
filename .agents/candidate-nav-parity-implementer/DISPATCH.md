# DISPATCH - candidate-nav-parity

## 2026-09-11 08:17 UTC
You are assigned task **candidate-nav-parity** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/candidate-nav-parity-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Close two candidate-page parity gaps in the Vue 3 SPA (`web/frontend/`):
the missing legacy task footer and the stale question-navigator cache.

### Acceptance criteria
1. `src/components/candidate/TaskPane.vue`: footer (`Previous` · `Reset task` ·
   `Task {taskNum} of {totalTasks}` · `Next`) rendered when a task exists,
   token-styled, `data-testid`s `task-footer`/`task-prev`/`task-next`/`task-reset`/
   `task-progress-text`, emits `prev`/`next`/`reset`.
2. Disable Previous when `taskNum <= 1`, Next when `totalTasks > 0 && taskNum >= totalTasks`,
   all three while `busy`.
3. `src/views/CandidateView.vue`: pass `task-num`/`total-tasks`/`busy`; handlers
   `onPrev`/`onNext` -> `session.prev()/next()` + error toast; `onResetTask` ->
   confirm + `session.retry()` + success/error toast.
4. `src/components/candidate/QuestionDrawer.vue`: uncontrolled + `loadOnOpen` open
   always calls `loadItems()` (no `loaded.length === 0` guard); in-flight guard;
   controlled mode unchanged.
5. Unit tests for footer emit/disable rules; E2E for next/prev and drawer refetch.
6. `bun run lint`, `bunx vue-tsc --noEmit`, `bun run test` (>=218), `npx playwright test`
   (20) all pass.

### Verification method
From `web/frontend/`:
`bun run lint`; `bunx vue-tsc --noEmit`; `bun run test`; `npx playwright test`.

### Constraints
- One focused change; strict parity (D-007); tokens only.
- Do not commit/push; do not touch out-of-scope paths.
- Update `EVIDENCE.md` with proof.
