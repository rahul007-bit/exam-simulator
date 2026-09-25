# EVIDENCE — FE-026

## Implementer — implementer-18 (2026-09-10 11:12 UTC)
- Deliverable: noVNC desktop island + 36px segmented Desktop/Terminal workspace
  control + noVNC URL/postMessage helpers.
- Files touched:
  - `web/frontend/src/composables/useVnc.ts` (new)
  - `web/frontend/src/components/workspace/NoVncFrame.vue` (new)
  - `web/frontend/src/components/workspace/WorkspaceTabs.vue` (new)
  - `.agents/FE-026-implementer-18/*` (metadata)
- Commands run + output:
  ```
  $ bunx vue-tsc --noEmit
  EXIT=0
  ```
  (One earlier invocation reported a transient error in the out-of-scope
  `src/components/admin/SessionActionsDialog.vue:134` from a concurrent agent's
  in-progress edit; the clean re-runs return EXIT=0.)

### noVNC URL/params contract used
Built in `useVnc.ts: buildNoVncUrl()` (query assembled manually to avoid
`URLSearchParams` percent-encoding `/`):

- Candidate (matches `web/static/js/app.js:1655`):
  ```
  /novnc/vnc.html?autoconnect=true&resize=remote&reconnect=true&path=ws/desktop/${encodeURIComponent(sid)}
  ```
- View-only/observe (matches `web/static/js/admin.js:778`):
  ```
  /novnc/vnc.html?autoconnect=true&resize=remote&reconnect=true&view_only=true&path=ws/desktop/${encodeURIComponent(sid)}
  ```
- Empty/null session id falls back to `active` (legacy `|| 'active'`).

iframe attributes (`NoVncFrame.vue`, matches `web/static/index.html:142`):
- `allow="clipboard-read *; clipboard-write *; fullscreen *; keyboard-map *"`
  (exported as `VNC_ALLOW`)
- `allowfullscreen` present (`allowfullscreen` boolean attribute).

postMessage contract (matches `web/static/js/app.js:156-167`, `:260-266`):
- outbound host → island: `{ type: 'SET_CLIPBOARD', text }`
- inbound island → host: `VNC_CLIPBOARD` (`text: string`), `VNC_DISCONNECTED`

- Screenshots: n/a (testing paused; browser legs deferred to platform host).
- Test cases executed (see TESTPLAN.md): T3 PASS, T4 PASS; T1/T2 DEFERRED.
- Self-check against acceptance criteria:
  1. desktop iframe URL/params match current behavior — PASS (static string
     equivalence to `app.js:1655`; runtime connect T1 deferred to host).
  2. tab switch preserves iframe state — PASS by construction (both islands stay
     mounted; `v-show` toggles visibility; `src` set once on first activation and
     never cleared). Runtime confirmation T2 deferred to host.
  3. clipboard/allowed attrs preserved — PASS (`VNC_ALLOW` verbatim,
     `allowfullscreen`, and the `SET_CLIPBOARD` / `VNC_CLIPBOARD` /
     `VNC_DISCONNECTED` message contract).

### Shared/integration notes (orchestrator)
- `WorkspaceTabs` is not yet wired into a page; needs candidate-page integration
  with the live `sessionId`.
- Desktop tab no longer triggers keyboard lock/fullscreen; that belongs to
  `useFullscreen` per PLAN §4/§5 — flagged, not implemented here.
- No consumer of `useVnc`'s `postMessage` bridge yet (clipboard composable FE-02x).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <pending>
- Re-ran acceptance commands: <pending>
- Test cases re-run independently (see TESTPLAN.md): <pending>
- Criterion-by-criterion result: <pending>
- Regression checks (WS, clipboard, timer, a11y, contrast): <pending>
- Verdict: <pending>
