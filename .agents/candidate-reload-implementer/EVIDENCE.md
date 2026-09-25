# EVIDENCE — candidate-reload

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-candidate-reload (2026-09-10 15:51 UTC)
- Deliverable: Working header overflow **Reload** action on the candidate page,
  matching legacy `reloadWorkspaceFrame` (`web/static/js/app.js:1726`): reconnect
  the terminal when the terminal tab is active, otherwise reload the noVNC frame.
- Files touched:
  - `web/frontend/src/views/CandidateView.vue`
  - `web/frontend/tests/unit/candidate-reload.test.ts` (new)
  - `.agents/candidate-reload-implementer/*` (this metadata)
- Exact reload wiring (`CandidateView.vue`):
  - `const workspaceTabs = ref<InstanceType<typeof WorkspaceTabs> | null>(null)` (line ~72)
  - `<WorkspaceTabs ref="workspaceTabs" :session-id="sessionId ?? 'active'" />` (template)
  - `onAction` `case 'reload'`:
    ```ts
    case 'reload': {
      const tabs = workspaceTabs.value
      if (!tabs) return
      if (tabs.activeTab === 'terminal') {
        tabs.terminal?.reconnect()
      } else {
        tabs.vnc?.reload()
      }
      return
    }
    case 'new-tab':
    default:
      return
    ```
  - `new-tab` left as its prior no-op. All other cases untouched.
- Commands run + output:
  ```
  > bunx vue-tsc --noEmit
  (no output — PASS, exit 0)

  > bun run lint
  (no output — PASS, exit 0, full workspace)

  > bunx eslint src/views/CandidateView.vue tests/unit/candidate-reload.test.ts
  (no output — PASS, exit 0)

  > bunx vitest run tests/unit/candidate-reload.test.ts
  ✓ tests/unit/candidate-reload.test.ts (3 tests) 46ms
  Test Files  1 passed (1)
       Tests  3 passed (3)
  ```
  Note: `bun run test` (full suite) was intentionally **not** run per dispatch
  (concurrent test agent); only the new scoped file was run. `bun run build` /
  Playwright were not run.
- Screenshots: n/a (unit-level wiring; no browser run permitted)
- Test cases executed (see TESTPLAN.md): T1 PASS, T2 PASS, T3 PASS
- Self-check against acceptance criteria:
  1. Reload reconnects terminal on terminal tab — pass (unit T1 asserts
     `terminal.reconnect()` called once and `vnc.reload()` not called).
  2. Reload reloads noVNC on desktop tab — pass (unit T2 asserts
     `vnc.reload()` called once and `terminal.reconnect()` not called).
  3. Missing ref / workspace unmounted is a safe no-op (never throws) — pass
     (unit T3; guard `if (!tabs) return`).
  4. Switch structure and other cases intact, `new-tab` unchanged — pass
     (diff-scoped edit; typecheck+lint clean).
  5. Exposed refs typed so `vue-tsc` passes — pass (`vue-tsc --noEmit` exit 0).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
