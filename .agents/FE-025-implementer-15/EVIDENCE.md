# EVIDENCE — FE-025

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-15 (2026-09-10 UTC)
- Deliverable: ref-driven XTerm island + `/ws/terminal` transport composable.
- Files touched (scope only):
  - `web/frontend/src/components/workspace/XTerm.vue` (new)
  - `web/frontend/src/composables/useTerminal.ts` (new)
  - `.agents/FE-025-implementer-15/**` (metadata)
- Commands run + output:
  ```
  $ Test-Path web/frontend/node_modules/@xterm/xterm   -> False
  $ Test-Path web/frontend/node_modules/@xterm/addon-fit -> False
  $ Select-String web/frontend/package.json -Pattern '@xterm' -> (no matches)
  $ bunx tsc --noEmit   (cwd: web/frontend)
  EXIT: 0
  ```
- Screenshots: n/a (testing paused; runtime requires the missing deps).
- Test cases executed (see TESTPLAN.md): T1 BLOCKED, T2 BLOCKED.
- Self-check against acceptance criteria:
  1. connects to `/ws/terminal/<sid>` — IMPLEMENTED. URL is built as
     `${ws|wss}//${location.host}/ws/terminal/${encodeURIComponent(sid)}` with a
     `/ws/terminal` fallback; `binaryType = 'arraybuffer'`.
  2. resize messages on container resize — IMPLEMENTED. `ResizeObserver` on the
     container (plus `window resize`) calls `FitAddon.fit()`; the resulting xterm
     `onResize` emits `{"resize":{"rows":R,"cols":C}}` via the composable, matching
     `web/server.py:1832`.
  3. scrollback buffer replayed on reconnect — IMPLEMENTED. Binary output is
     retained in a bounded (200-chunk) plain array; `replayScrollback()` re-writes
     it to the terminal. The server also replays Redis scrollback on connect
     (`web/server.py:1758`), so parity is preserved.
- **Blocker (INCOMPLETE for runtime):** `@xterm/xterm` and `@xterm/addon-fit`
  are not installed and the batch rules forbid installing them or editing
  `package.json`. `XTerm.vue` statically imports both (correct idiomatic form), so
  `vue-tsc` / `vite build` will fail until the orchestrator adds
  `@xterm/xterm@5.5.0` + `@xterm/addon-fit@0.10.0`. `bunx tsc --noEmit` passes
  because plain `tsc` does not compile `.vue` SFCs.

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <pending dependency install>
- Re-ran acceptance commands:
  ```
  <pending>
  ```
- Test cases re-run independently (see TESTPLAN.md): <pending>
- Criterion-by-criterion result:
  1. connects to `/ws/terminal/<sid>` — <pending>
  2. resize frames on container resize — <pending>
  3. scrollback replay on reconnect — <pending>
- Regression checks (WS, clipboard, timer, a11y, contrast): <pending>
- Verdict: <pending> — cannot be `verified` until `@xterm/*` are installed and
  the WS interaction is exercised.
