# EVIDENCE - candidate-nav-parity

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer - candidate-nav-parity-implementer (2026-09-11 08:17 UTC)

### Deliverable
1. **Task footer** in `TaskPane.vue` (FE-022): renders when a task exists, below
   the scrollable markdown area, token-styled (`border-t border-border`), with
   `Previous` / `Reset task` / `Task {taskNum} of {totalTasks}` / `Next`. Emits
   `prev`/`next`/`reset` (plus existing `copy`). Previous disabled when
   `taskNum <= 1`; Next disabled when `totalTasks > 0 && taskNum >= totalTasks`;
   all three disabled while `busy`. `data-testid`s: `task-footer`, `task-prev`,
   `task-next`, `task-reset`, `task-progress-text`.
2. **Wiring** in `CandidateView.vue`: passes `:task-num="currentTask"`,
   `:total-tasks="totalTasks"`, `:busy="session.loading"`; `onPrev`/`onNext` call
   `session.prev()`/`session.next()` and push an error toast on failure;
   `onResetTask` shows the async `confirm({... danger:true})` then `session.retry()`
   and pushes success/error toasts. Non-blocking (no native dialogs).
3. **Stale navigator fix** in `QuestionDrawer.vue`: the `modelValue` watcher now
   always calls `loadItems()` when `open && !controlled && loadOnOpen` (removed
   the `loaded.value.length === 0` guard), matching legacy
   `openQuestionDrawer()`; `loadItems()` has an in-flight guard
   (`if (internalLoading.value) return`). Controlled mode (`questions` prop)
   unchanged.

### Files touched
- `web/frontend/src/components/candidate/TaskPane.vue`
- `web/frontend/src/components/candidate/QuestionDrawer.vue`
- `web/frontend/src/views/CandidateView.vue`
- `web/frontend/tests/unit/task-pane.test.ts` (new, 5 tests)
- `web/frontend/tests/unit/question-nav.test.ts` (extended, +1 test)
- `web/frontend/tests/e2e/candidate-journey.spec.ts` (extended)
- `web/frontend/tests/e2e/helpers.ts` (stateful next/prev/jump/retry + retry mocks)

### Commands run + output
From `web/frontend/`:

```
$ bun run lint
$ eslint .
(no errors)

$ bunx vue-tsc --noEmit
(no errors)

$ bun run test
Test Files  21 passed (21)
     Tests  224 passed (224)          # baseline 218 + 6 new

$ npx playwright test
17 passed, 3 failed                  # confirm/theme/toast

$ npx playwright test tests/e2e/confirm.spec.ts tests/e2e/theme.spec.ts tests/e2e/toast.spec.ts
2 passed, 2 failed                   # confirm passes in isolation; theme/toast fail

$ npx playwright test --config playwright.isolated.config.ts   # transient, deleted after
20 passed (5.0s)
```

### Environment note (why the default `npx playwright test` was not green)
The host has a **live candidate session** on the backend proxied by the
(reused) Vite dev server on `:5173`:

```
GET http://localhost:5173/api/session -> 200
{"active":true,"session_id":"session-1789112771","name":"Easy Set 04 - Speed Run",
 "current_index":2,"total_tasks":17,...}
```

`confirm.spec.ts`, `theme.spec.ts` and `toast.spec.ts` do **not** mock
`/api/session`, so they pick up that real active session; `FullscreenGuard`
then shows the `EXAM LOCKED: FULLSCREEN REQUIRED` overlay which intercepts the
clicks (`theme`/`toast`) and briefly mis-focused the confirm button. This is
environmental and unrelated to this change (none of the touched files feed
those tests). To prove no regression, the full suite was run on a **fresh**
dev server on `:5174` with `VITE_BACKEND=http://127.0.0.1:9` (dead) via a
transient config, leaving the shared `:5173` server untouched: **20 passed**.
The transient config was deleted (`git status` shows no config change).

### Screenshots
n/a (CLI + Playwright assertions).

### Test cases executed (see TESTPLAN.md)
T1 PASS, T2 PASS, T3 PASS, T4 PASS, T5 PASS, T6 PASS, T7 PASS.

### Self-check against acceptance criteria
1. Footer rendered/emitted/disabled - PASS (`task-pane.test.ts`, E2E T3).
2. CandidateView wiring - PASS (typecheck + E2E T3 task-next/prev).
3. Drawer refetch on every open - PASS (`question-nav.test.ts` T2 + E2E reopen).
4. Tests + all verify commands - PASS (isolated E2E 20/20; unit 224/224).

## Verifier - <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> - PASS/FAIL - <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` - <reasons if rejected>
