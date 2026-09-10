# DISPATCH — FE-035

## 2026-09-10T11:28:58Z
You are assigned task **FE-035** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-035-implementer-25`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Admin live observe view: `useObserve` (explicit-session terminal + view-only
desktop observe, detail polling, reset/terminate/end mutations) and
`ObserveOverlay.vue` (full-screen overlay reusing the XTerm + NoVNC islands, with
Reset/End via `useConfirm` + toast).

### Acceptance criteria
1. observe connects to the selected session only
2. admin reset/end available in observe
3. no cross-session leakage

### Verification method
- `bunx vue-tsc --noEmit` (testing paused; tsc only during the batch).
- Static audit: no `active`/`default` fallback in the observe targets; every URL
  derives from the explicit `sessionId`.
- Deferred (host-only): observe an active session; attempt cross-session attach.

### Constraints
- Only `web/frontend/src/composables/useObserve.ts` (new) and
  `web/frontend/src/components/admin/ObserveOverlay.vue` (new) may change.
- `AdminView.vue` is untouched — the orchestrator wires the overlay.
- Preserve parity behavior (WS, timer, token routing) and admin WS attach rules.
- Update `EVIDENCE.md` with proof.
