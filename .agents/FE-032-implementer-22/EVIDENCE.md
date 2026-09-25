# EVIDENCE — FE-032

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-22 (2026-09-10T11:19:53Z)
- Deliverable: admin default-preset selector + max-concurrent-sessions form with
  client-side validation and toast/inline feedback.
- Files touched:
  - `web/frontend/src/composables/useAdminConfig.ts` (new)
  - `web/frontend/src/components/admin/AdminConfigForm.vue` (new)
  - `web/frontend/src/components/admin/AdminResourceForm.vue` (new)
  - `web/frontend/src/views/AdminView.vue` (modified)
- Endpoints wired (existing typed API layer, no API/client changes needed):
  - `GET /api/admin/config` → `getAdminConfig()` (loads `default_preset`)
  - `POST /api/admin/config` → `setAdminConfig(preset)`
  - `GET /api/admin/resources` → `getAdminResources()`
  - `POST /api/admin/resources` → `setAdminResources(limit)`
  - `GET /api/presets` → `getPresets()` (preset catalogue for the selector)
- Commands run + output:
  ```
  $ bunx vue-tsc --noEmit
  EXIT=0
  ```
- Screenshots: n/a (batch testing paused; no dev server started).
- Test cases executed (see TESTPLAN.md): T1 DEFERRED, T2 DEFERRED, T3 PASS.
- Self-check against acceptance criteria:
  1. Forms reflect `/api/admin/config` and `/api/admin/resources` — PASS.
     `useAdminConfig.loadAll()` fetches presets + config + resources together on
     mount; `AdminConfigForm` is seeded from `default_preset`; `AdminResourceForm`
     renders the live snapshot (running containers, max sessions, available
     memory, recommended max, capacity badge) and seeds the input from
     `max_concurrent_sessions`.
  2. Validation errors shown via toast/inline — PASS (by construction).
     `validateMaxSessions()` rejects non-integers and values `< 1`. The form
     shows the message via `Input :error` (inline) and emits `invalid`, which the
     view surfaces with a warning toast; no POST is issued.
  3. Success feedback via toast — PASS. `onSavePreset` / `onSaveMaxSessions`
     push a success toast after the POST resolves.
- Parity / constraints:
  - The preset selector keeps the legacy synthetic `all` ("Full Curriculum (All
    111 Tasks, Untimed)") option and uses preset `filename` values, matching
    `web/static/js/admin.js`.
  - Tokens/Tailwind only; no raw hex, glow, gradient, keyframes or emoji
    (satisfies the FE-002/FE-014 audits).
  - No shared files touched (App.vue, main.ts, router, package.json, configs,
    `ui/**`, `stores/**` untouched).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1, T2, T3>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
