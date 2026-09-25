# EVIDENCE — FE-027

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-20 (2026-09-10 11:17 UTC)
- Deliverable: `useClipboard` composable + headless `ClipboardBridge.vue`.
- Files created:
  - `web/frontend/src/composables/useClipboard.ts`
  - `web/frontend/src/components/workspace/ClipboardBridge.vue`
- Files read only (not modified): `useVnc.ts`, `NoVncFrame.vue`,
  `WorkspaceTabs.vue`, `CandidateView.vue`, `useTimer.ts`, `stores/session.ts`,
  `useToast.ts`, `web/static/js/app.js`, `web/server.py`.
- Commands run + output:
  ```
  $ bunx vue-tsc --noEmit
  # (final run) exit 0 — no output
  ```
  An intermediate run showed three diagnostics in `src/composables/useFullscreen.ts`
  (owned by the concurrently-running FE-028 / implementer-21); none originated from
  either FE-027 file, and the final run after that agent's fix is clean.
- Screenshots: n/a (testing paused per batch rules; browser legs host-only).
- Test cases executed (see TESTPLAN.md): T1 DEFERRED, T2 DEFERRED, T3 DEFERRED
  (batch rules suspend `bun run test` / Playwright; only `bunx vue-tsc` permitted).
- Self-check against acceptance criteria:
  1. Host↔desktop copy — ported `syncTextToVnc` (`app.js:256`),
     `handleIncomingVncClipboard` (`app.js:400`), `syncFromVncClipboard`
     (`app.js:436`), `copyFromDesktopToHost` (`app.js:459`) — code-complete; manual
     browser check DEFERRED to host verifier.
  2. Pending-flush preserved — `pendingHostClipboardText` set when
     `navigator.clipboard.writeText` rejects; flushed on `click`/`pointerdown`/
     `keydown` (capture, passive) via `flushPendingHostClipboard()` mounted by the
     bridge (mirrors `app.js:120-130`).
  3. No busy polling — `syncFromVnc()` returns early when `connected.value` is
     true and not an explicit action; the 5s fallback interval also short-circuits
     on `connected` (`app.js:113-118`). `POST /api/clipboard` is used only when the
     socket is not OPEN (`syncTextToVnc` step 3).

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
