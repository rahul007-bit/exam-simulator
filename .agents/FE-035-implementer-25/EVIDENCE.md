# EVIDENCE — FE-035

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-25 (2026-09-10T11:28:58Z)

### Deliverable
Admin live observe view, reusing the existing imperative islands against a single
explicit session:
- `useObserve.ts` — explicit-session terminal WS path + view-only noVNC URL,
  `/api/admin/session/{sid}` detail polling/refresh, and
  terminate/reset/end mutations.
- `ObserveOverlay.vue` — full-screen overlay (Desktop/Terminal tabs) that mounts
  `NoVncFrame` (view-only) and `XTerm`, with Reset/End admin controls routed
  through `useConfirm` + `useToast`.

### Files touched
- `web/frontend/src/composables/useObserve.ts` (new)
- `web/frontend/src/components/admin/ObserveOverlay.vue` (new)
- `.agents/FE-035-implementer-25/**` (workspace metadata only)

No shared/config/`ui/**`/`layout/**`/`workspace/**`/`candidate/**`/`stores/**`
files touched. `AdminView.vue` untouched (wiring notes below).

### Public API — `useObserve`
```ts
useObserve({ sessionId, active?, pollIntervalMs? = 5000, autoStart? = true })
  -> {
    sessionId: ComputedRef<string | null>,
    detail: Ref<ObserveSessionDetail | null>,
    loading: Ref<boolean>, refreshing: Ref<boolean>, error: Ref<string | null>,
    pendingAction: Ref<ObserveAction | null>,
    ready: ComputedRef<boolean>,
    terminalWsPath: ComputedRef<string>,   // /ws/terminal/<encodeURIComponent(sid)>
    desktopUrl: ComputedRef<string>,       // /novnc/vnc.html?...&view_only=true&path=ws/desktop/<sid>
    fetchDetail, refresh, runAction,       // runAction('terminate'|'reset'|'end')
    startPolling, stopPolling, dispose,
  }
```
Endpoints used:
- detail: `GET /api/admin/session/{sid}` (singular route)
- mutations: `POST /api/admin/sessions/{sid}/{terminate|reset|end}` (plural route)
- terminal WS: `/ws/terminal/<sid>` (island `XTerm` via `useTerminal`)
- desktop WS: `/novnc/ws/desktop/<sid>` via the view-only noVNC iframe

### Public API — `ObserveOverlay.vue`
- Props: `open: boolean`, `sessionId: string`, `sessionName?: string`
- Emits: `close: []`, `action: [{ action: ObserveAction; result: ObserveActionResult }]`

### Cross-session safety
- `normaliseSessionId` rejects blank/whitespace ids (`ready === false`); the
  islands are **not mounted** in that state (`data-testid="observe-empty"`), so
  the legacy noVNC `active` sentinel and the admin `/ws/terminal` with no sid
  (server closes 1008) are unreachable from this view.
- `desktopUrl` returns `''` when unset (never calls `buildNoVncUrl` with an empty
  id, which would otherwise fall back to `active`).
- Detail requests carry a monotonically increasing `requestToken`; a response is
  discarded unless it matches the current session id, so a late response for a
  previously observed session can never populate the panel.
- All routes are built from the single explicit getter — no `active`/`default`
  fallback anywhere.

### Commands run + output
```
PS web/frontend> bunx vue-tsc --noEmit
(no output)
EXIT=0
```
```
PS repo> Select-String observe sources -Pattern "#[0-9a-fA-F]{3,8}"
(no output)  # no raw hex
PS repo> Select-String observe sources -Pattern "box-shadow|text-shadow|drop-shadow|glow|linear-gradient"
only the doc-comment phrase "no raw hex, glow or emoji"  # no glow/gradient use
```
No emoji present in either file.

### Screenshots
n/a — browser leg DEFERRED (testing paused for this batch).

### Test cases executed (see TESTPLAN.md)
T1 DEFERRED (browser, host-only), T2 DEFERRED (browser, host-only),
T3 PASS, T4 PASS, T5 PASS.

### Self-check against acceptance criteria
1. observe connects to the selected session only — PASS: `XTerm :session-id` and
   `NoVncFrame :session-id` bind the explicit prop; `terminalWsPath`/`desktopUrl`
   derive solely from it; empty id renders the disabled empty state.
2. admin reset/end available in observe — PASS: header Reset/End buttons run
   through `useConfirm`, call `POST /api/admin/sessions/{sid}/reset|end`, and
   report via `useToast`; per-action `pendingAction` disables only its own button.
3. no cross-session leakage — PASS: explicit-only targets + request-token guard +
   no `active`/`default` fallback (see Cross-session safety).

### Integration notes for `AdminView.vue` (orchestrator-owned)
1. `import ObserveOverlay from '@/components/admin/ObserveOverlay.vue'`.
2. Add `const observeOpen = ref(false)` and `const observeTarget = ref<AdminSessionItem | null>(null)`.
3. Offer "Observe" only for rows that have `type === 'active'` **and** a
   `session_id` (invites/archived rows have no live session). Set
   `observeTarget.value = row; observeOpen.value = true`.
4. Render:
   ```vue
   <ObserveOverlay
     :open="observeOpen"
     :session-id="observeTarget?.session_id ?? ''"
     :session-name="observeTarget?.name ?? ''"
     @close="observeOpen = false"
     @action="onObserveAction"
   />
   ```
5. `onObserveAction({ action, result })`: close on `terminate`; refresh the table
   via `fetchSessions({ silent: true })` (already non-blocking per FE-036); for
   `end`, surface `result.scorecard` through the existing scorecard view if
   desired.
6. The overlay mounts its islands only while `open` and a concrete id exists, so
   closing it tears down the terminal socket and noVNC iframe automatically.

---

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 ... , T2 ..., T3 ...>
- Criterion-by-criterion result:
  1. selected-session-only — PASS/FAIL — <evidence>
  2. reset/end available — PASS/FAIL — <evidence>
  3. no cross-session leakage — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
