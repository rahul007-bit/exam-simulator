# TESTPLAN - FE-028

Per-task test plan. Browser legs are host-only and were paused for this batch;
they are marked **DEFERRED** and must be resolved at the M3 gate.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | manual | start exam then exit fullscreen | warning overlay shown | DEFERRED (browser paused); logic traced: `fullscreenchange` -> `showWarningIfNeeded()` -> `warningVisible=true` when `isActive && !isAdmin` | |
| T2 | manual | admin mode fullscreen | no lock enforced | DEFERRED; `shouldEnforceFullscreen()` returns false when `isAdmin` (policy bypass) | |
| T3 | manual | Firefox unsupported lock | degrades without breaking exam | DEFERRED; `getKeyboard()` returns null -> `requestKeyboardLock()` returns false; all calls try/catch'd | |
| T4 | audit | `bunx vue-tsc --noEmit` | exit 0 | PASS (exit 0, 2026-09-10) | |
| T5 | audit | scan new files for raw hex / emoji / glow / gradient | none | PASS (0 hex, 0 emoji; only non-ASCII are `§` and em dash) | |

## Edge cases / additions
- `requestFullscreen()` rejection (permission/policy) -> `enterFullscreen()` resolves `false`, no throw.
- `navigator.keyboard.lock()` rejection (no user activation) -> swallowed, `keyboardLockActive=false`.
- Safari/older WebKit `webkitRequestFullscreen` / `webkitExitFullscreen` handled; promise not assumed.
- No `document` / `navigator` (SSR/jsdom) -> capability detectors return false and listeners no-op.
- Re-entry button click is a user gesture, so `reenterFullscreen()` can re-acquire fullscreen.
- Warning only shows while an exam is active and the user is not an admin; ending/reseting hides it.
- `stopFullscreenGuard()` on unmount releases the keyboard lock and detaches all listeners.

## Environment
- Commit / build: e0fb4a3 (branch `feature/frontend-vue-migration`)
- Host: local (win32, Bun + vue-tsc)
- Browser(s): Chrome/Firefox DEFERRED (paused per batch rules)

## Verdict
- Implementer: PASS (typecheck) / manual legs DEFERRED, 2026-09-10
- Verifier: <pending>
