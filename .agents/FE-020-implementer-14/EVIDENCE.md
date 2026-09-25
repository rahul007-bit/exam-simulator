# EVIDENCE — FE-020

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-14 (2026-09-10 11:01 UTC)

### Deliverable
Slim candidate shell + 52px header. New layout components under
`src/components/layout/` and the candidate route wired to them.

### Files touched
- `web/frontend/src/components/layout/types.ts` (new)
- `web/frontend/src/components/layout/menu.ts` (new)
- `web/frontend/src/components/layout/OverflowMenu.vue` (new)
- `web/frontend/src/components/layout/AppHeader.vue` (new)
- `web/frontend/src/components/layout/AppShell.vue` (new)
- `web/frontend/src/components/layout/index.ts` (new)
- `web/frontend/src/views/CandidateView.vue` (modified: placeholder → shell)

No other files were created or modified in this task.

### Commands run + output
```
$ bunx tsc --noEmit
EXIT=0

$ grep -nE "#[0-9a-fA-F]{3,6}|text-shadow|box-shadow" \
    src/components/layout src/views/CandidateView.vue
(no matches)
```
Browser (Playwright) checks are **DEFERRED** — PROTOCOL §6: host-only, and the
batch rule is typecheck-only (`bunx tsc --noEmit`).

### Component API
- **AppShell** (`layout/AppShell.vue`)
  - props: `examName`, `active`, `currentTask`, `totalTasks`, `flagged`,
    `isAdmin`, `sessionId`, `submitting`, `canViewRecordings`,
    `showQuestionDrawer`.
  - emits: `flag`, `submit`, `expired`, `action(id)`, `select-task(taskNum)`.
  - owns FE-023 `useTimer({ url, autoConnect, onExpired })`; starts/stops with
    `active`; default slot = workspace; renders FE-024 `QuestionDrawer`.
- **AppHeader** (`layout/AppHeader.vue`)
  - props: `examName`, `active`, `currentTask`, `totalTasks`, `flagged`,
    `isAdmin`, `sessionId`, `timerText`, `timerUrgency`, `submitting`,
    `canViewRecordings`.
  - emits: `flag`, `submit`, `open-questions`, `action(id)`.
  - primary row: exam name (truncated) · progress button · timer slot · Flag ·
    Submit exam · `⋯` overflow.
- **OverflowMenu** (`layout/OverflowMenu.vue`)
  - props: `items: HeaderMenuItem[]`, `label`, `align`, `disabled`.
  - emits: `select(id)`. Headless UI `Menu` (menu roles, roving focus, Escape,
    outside-click). `data-testid="header-overflow[-menu]"`.
- **Pure helpers** (`layout/menu.ts`): `buildOverflowMenu(options)` and
  `progressLabel(progress)`.

Overflow order (legacy parity, `web/static/index.html:39-65`):
`Copy session ID` (disabled until a session exists) → `Fullscreen` → `Reload` →
`New tab` → `Copy from Desktop` → `Recordings & review` (admin-gated) →
admin-only `End exam` / `Reset exam`.

### Self-check against acceptance criteria
1. **Only primary controls in the header; secondary in one overflow** — PASS by
   construction: `AppHeader.vue:87-157` renders name/progress/timer/Flag/Submit +
   the single `OverflowMenu`; all other actions come from
   `buildOverflowMenu` (`menu.ts:18-52`). Browser confirmation DEFERRED.
2. **Session-id copy + admin End/Reset moved to overflow** — PASS:
   `copy-session-id` is the first overflow row; `admin-end`/`admin-reset` are
   appended only when `isAdmin` (`menu.ts:40-50`). CandidateView routes
   `copy-session-id`/`admin-end`/`admin-reset` (`CandidateView.vue:124-156`).
3. **Responsive 1366x768 / 1920x1080, no overflow/clipping** — PASS by layout:
   name is `min-w-0 truncate` inside a `flex-1`, controls are `flex-none`, header
   is fixed `h-[var(--header-height)]`, and the panel is absolutely positioned.
   Screenshot confirmation DEFERRED (browser/host-only).

### TODO(integration) (deliberately not implemented — owned by other tasks)
- `AppShell`: full session event bus (`clipboard_update`, `transition_progress`,
  `session_expired`, `session_terminated`) via `useTimer().handleMessage()`.
- `CandidateView.onAction`: `fullscreen` → FE-028; `reload`/`new-tab` → FE-026;
  `copy-from-desktop` → FE-027; `recordings` → FE-029.
- `CandidateView` workspace right pane: FE-021 split-pane + FE-025 XTerm /
  FE-026 NoVncFrame.

### Shared-file changes needed (not edited — orchestrator owns)
- `src/App.vue` currently renders a global `.app-topbar` (brand + ThemeToggle)
  above `<RouterView/>`. On the candidate route this stacks a second bar above
  the 52px `AppHeader`. It should be removed for the candidate route (or moved
  into the shell) so there is exactly one header.
- `src/App.vue` sets `.app-shell { min-height: 100% }` with a flex column and no
  fixed height; `AppShell` uses `h-full min-h-0`, which needs the app shell to be
  full-viewport (`height: 100%`/`h-screen`) for correct filling. Adjust once the
  topbar is removed.

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
