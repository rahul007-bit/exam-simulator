# EVIDENCE - FE-028

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer - implementer-21 (2026-09-10 11:18 UTC)
- Deliverable: `useFullscreen` composable + `FullscreenGuard.vue` overlay.
- Files touched (only in-scope):
  - `web/frontend/src/composables/useFullscreen.ts` (new)
  - `web/frontend/src/components/FullscreenGuard.vue` (new)
- Commands run + output:
  ```
  $ bunx vue-tsc --noEmit
  (no output) EXIT=0
  ```
- Screenshots: n/a (browser testing paused per batch rules).
- Test cases executed (see TESTPLAN.md): T4 PASS, T5 PASS; T1/T2/T3 DEFERRED (browser).
- Self-check against acceptance criteria:
  1. **Warning overlay shows on fullscreen exit** - PASS by code path:
     `handleFullscreenChange` (`useFullscreen.ts:202`) sets `warningVisible =
     shouldEnforceFullscreen()` on exit; `FullscreenGuard.vue` renders whenever
     `warningVisible` is true. Browser leg DEFERRED.
  2. **Candidate mode enforces lock; admin bypass** - PASS by code path:
     `shouldEnforceFullscreen()` (`:177`) = `!policyIsAdmin() && policyIsActive()`;
     `useFullscreen({ isAdmin, isActive })` wires both getters. Admin -> no
     overlay/no input guards. Browser leg DEFERRED.
  3. **Graceful on unsupported browsers** - PASS by code path: every capability is
     feature-detected (`isFullscreenSupported`, `isKeyboardLockSupported`,
     `requestFullscreenFn`) and every async call is wrapped in `try/catch`; absent
     APIs are no-ops. Browser leg DEFERRED.

### Public API
```ts
useFullscreen(options?: {
  isAdmin?: MaybeRefOrGetter<boolean>   // admin bypass (default false)
  isActive?: MaybeRefOrGetter<boolean>  // overlay only while exam live
  target?: () => Element | null         // default documentElement
  autoStart?: boolean                   // default true
}): {
  isFullscreen: Readonly<Ref<boolean>>
  warningVisible: Readonly<Ref<boolean>>   // consumed by FullscreenGuard
  keyboardLockActive: Readonly<Ref<boolean>>
  supported: ComputedRef<boolean>
  keyboardLockSupported: ComputedRef<boolean>
  enter(): Promise<boolean>          // call synchronously from the Start click
  exit(): Promise<void>
  toggle(): Promise<void>            // overflow "Fullscreen" action
  reenter(): Promise<boolean>        // overlay button
  hideWarning(): void
  requestKeyboardLock(): Promise<boolean>
  releaseKeyboardLock(): void
}
```
Also exported as standalone functions: `isFullscreenSupported`,
`isKeyboardLockSupported`, `requestKeyboardLock`, `releaseKeyboardLock`,
`enterFullscreen`, `exitFullscreen`, `toggleFullscreen`,
`shouldEnforceFullscreen`, `showWarningIfNeeded`, `hideWarning`,
`reenterFullscreen`, `startFullscreenGuard`, `stopFullscreenGuard`.

### Browser-fragility notes (Chrome vs Firefox)
- **Chrome/Edge:** `Element.requestFullscreen()` + `navigator.keyboard.lock()`
  available. `lock()` needs a fullscreen document *and* transient user
  activation; the `Start` click provides it. If it rejects we swallow the error
  (`keyboardLockActive=false`) and the exam continues.
- **Firefox:** fullscreen works; Keyboard Lock (`navigator.keyboard`) is not
  exposed -> `getKeyboard()` returns `null`, `requestKeyboardLock()` returns
  `false`, no throw. Fullscreen enforcement + overlay still work.
- **Safari/WebKit:** prefixed `webkitRequestFullscreen` / `webkitExitFullscreen` /
  `webkitFullscreenElement` are handled; their return values are not assumed to
  be promises.
- **SSR/jsdom:** no `document`/`navigator` -> supported=false, listeners no-op.

### Integration / wiring notes for the orchestrator
1. Mount `<FullscreenGuard />` once in the candidate tree (e.g. alongside
   `Toaster`/`ConfirmDialog` in `CandidateView.vue`; it `Teleport`s itself to
   `body`, so placement is flexible). It shares the module singleton state.
2. In `CandidateView.vue`, create the policy once:
   ```ts
   import { useFullscreen } from '@/composables/useFullscreen'
   const fullscreen = useFullscreen({
     isAdmin: computed(() => session.isAdmin),
     isActive: active,
   })
   ```
   Then call `fullscreen.enter()` **synchronously** at the top of `onStart`
   and `onPresetSelect` (user-gesture requirement), mirroring legacy
   `startAssignedExam` -> `enterCandidateFullscreen()`.
3. Replace the `case 'fullscreen':` placeholder in `onAction` (`CandidateView.vue:167`)
   with `await fullscreen.toggle()`.
4. For rejoin/reload parity: after `fetchSession()` resolves to an active
   session, the internal `watch([isAdmin, isActive])` calls
   `showWarningIfNeeded()`, which shows the overlay if the user is not already
   fullscreen (legacy `app.js:563-566`). No extra call required.
5. Scope note: the global `contextmenu`/devtools blockers are gated on
   `shouldEnforceFullscreen()` (active candidate exam), so mounting the guard on
   the candidate route will not affect admin/login pages.

## Verifier - <different agent> (<UTC>)
- Clean checkout / environment:
- Re-ran acceptance commands:
- Test cases re-run independently (see TESTPLAN.md):
- Criterion-by-criterion result:
- Regression checks (WS, clipboard, timer, a11y, contrast):
- Verdict: <verified | rejected>
