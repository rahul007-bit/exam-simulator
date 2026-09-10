# EVIDENCE — FE-036

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-19 (2026-09-10T11:12:29Z)

### Deliverable
Admin reset/terminate/end UX: tighter, consistent dialog spacing + non-blocking
(GCP-style) per-row loading so one in-flight action never locks or blanks the rest
of the admin sessions page.

### Files touched
- `web/frontend/src/composables/useAdminSessions.ts` (modified)
- `web/frontend/src/views/AdminView.vue` (modified)
- `web/frontend/src/components/admin/SessionActionsDialog.vue` (modified)
- `web/frontend/src/components/ui/Modal.vue` (modified)
- `web/frontend/src/components/ConfirmDialog.vue` (modified)
- `.agents/FE-036-implementer-19/**` (workspace metadata only)

No shared/config/other `ui/**` files touched. No changes requested.

### New per-row pending API (`useAdminSessions`)
```ts
pendingById: Ref<Map<string, SessionAction>>   // identifier -> in-flight action
anyPending: ComputedRef<boolean>               // size > 0 (reference only)
isRowPending(identifier: string): boolean
pendingActionFor(identifier: string): SessionAction | undefined
isPending(identifier: string, action: SessionAction): boolean
loading: Ref<boolean>      // initial load only -> DataTable :loading
refreshing: Ref<boolean>   // background refresh -> rows stay mounted
runAction(identifier, action)  // sets/clears per-row entry; fetchSessions({ silent: true })
```
`busy`/`pendingAction` (single global flag) removed.

### Spacing values (before → after)
| Element | Before | After |
| :--- | :--- | :--- |
| `Modal.vue` DialogPanel | `p-5` | `p-4` |
| `Modal.vue` body wrapper | `mt-4` | `mt-3` |
| `Modal.vue` footer | `mt-5` | `mt-3` |
| `ConfirmDialog.vue` DialogPanel | `p-5` | `p-4` |
| `ConfirmDialog.vue` title | `mb-2` | `mb-1.5` |
| `ConfirmDialog.vue` description | `mb-4` | `mb-3` |
| `ConfirmDialog.vue` prompt input | `mb-4` | `mb-3` |
| `SessionActionsDialog.vue` container | `gap-4` | `gap-3` |
| `SessionActionsDialog.vue` `<dl>` rows | `gap-y-2` | `gap-y-1.5` |
| `SessionActionsDialog.vue` action section | `pt-4` | `pt-3` |
All `data-testid`s and the Headless UI `Dialog` wiring (focus trap, Escape,
`aria-modal`/`aria-labelledby`/`aria-describedby`) are unchanged; ConfirmDialog's
focus/Escape behavior untouched.

### Non-blocking behavior
- `AdminView.onRowClick` no longer returns on a global `busy`; any row opens
  while another row is pending.
- `DataTable :loading="loading"` — initial load only. Post-mutation refresh uses
  `{ silent: true }` → `refreshing`, so rows stay visible.
- The affected row's Actions cell renders an inline spinner + label
  (`Resetting…`/`Ending…`/`Terminating…`) via a VNode (TanStack `FlexRender`
  supports VNodes). `DataTable.vue` itself was not modified (out of scope).
- `SessionActionsDialog` receives `pendingAction`; a pending action disables that
  row's action buttons and shows the spinner on the specific pending one. The
  **Close** button is never disabled.
- Refresh is disabled only while its own fetch runs (`refreshing || loading`).
- Sign out is no longer blocked by pending row actions.

### Commands run + output
```
PS> bunx vue-tsc --noEmit
(no output)
EXIT=0
```
```
PS> Select-String -Path useAdminSessions.ts, AdminView.vue, SessionActionsDialog.vue, Modal.vue, ConfirmDialog.vue `
      -Pattern "window\.confirm|window\.alert|[^.\w]alert\("
(no matches)
```

### Screenshots
n/a — browser leg DEFERRED (testing paused).

### Test cases executed (see TESTPLAN.md)
T1 PASS (logic/audit), T2 DEFERRED (browser, host-only), A1 PASS, A2 PASS, A3 PASS.

### Self-check against acceptance criteria
1. tighter, consistent dialog spacing — PASS (see table above).
2. per-row/inline busy without blocking other sessions — PASS: per-identifier
   `Map`, no global busy guard, inline spinner in the Actions cell.
3. table stays populated during mutation; only affected row disabled — PASS:
   `loading` is initial-only; `runAction` refreshes silently; dialog disables only
   that row's action buttons, Close stays live.
4. toast + promise confirm retained, no native dialogs — PASS: `useConfirm` +
   `useToast` unchanged; audit found no `window.confirm`/`alert`.

### Parity / notes
- Endpoints unchanged: `POST /api/admin/sessions/{identifier}/terminate|reset|end`.
- Identifier resolution unchanged (`session_id ?? candidate_token`).
- `DataTable.vue` not modified (only `ui/Modal.vue` per ownership); inline busy
  uses a VNode cell accepted by `FlexRender` (`isVNode` branch in
  `@tanstack/vue-table` `flexRender`).

---

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
