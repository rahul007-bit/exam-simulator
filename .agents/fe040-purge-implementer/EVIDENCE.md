# EVIDENCE — FE-040 (legacy removal / static cutover, part 1: frontend purge)

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-fe040-purge (2026-09-10T18:07:23Z)
- Deliverable: Strict purge of every legacy vanilla-JS reference from
  `web/frontend/**` (comments/tests/docs only). No runtime behaviour changed.
  Rewrote comments to keep the D-007 parity meaning while dropping dead
  `web/static/*`, `app.js`, `admin.js`, `admin.html`, `style.css` paths and
  `file:line` citations.
- Files touched (17, 68 insertions / 69 deletions):
  - `web/frontend/src/composables/useClipboard.ts`
  - `web/frontend/src/composables/useVnc.ts`
  - `web/frontend/src/composables/useFullscreen.ts`
  - `web/frontend/src/composables/useObserve.ts`
  - `web/frontend/src/composables/useReplay.ts`
  - `web/frontend/src/composables/useAdminInvites.ts`
  - `web/frontend/src/composables/useAdminSessions.ts`
  - `web/frontend/src/components/FullscreenGuard.vue`
  - `web/frontend/src/components/admin/ObserveOverlay.vue`
  - `web/frontend/src/components/candidate/question.ts`
  - `web/frontend/src/components/layout/menu.ts`
  - `web/frontend/src/components/workspace/ClipboardBridge.vue`
  - `web/frontend/src/components/workspace/NoVncFrame.vue`
  - `web/frontend/src/components/workspace/ReplayPlayer.vue`
  - `web/frontend/src/components/workspace/WorkspaceTabs.vue`
  - `web/frontend/src/stores/timer.ts`
  - `web/frontend/tests/unit/candidate-reload.test.ts`
- Commands run + output:
  ```
  # Worklist (before) — 35 hits; after — zero
  git grep -n -E 'web/static|static/js|static/css|app\.js|admin\.js|admin\.html|style\.css' -- web/frontend
  -> (no output) => ZERO HITS

  git grep -n -E 'app\.js:[0-9]+|admin\.js:[0-9]+|index\.html:[0-9]+' -- web/frontend
  -> (no output) => ZERO LEGACY CITATIONS

  # From web/frontend/
  bun run lint          -> $ eslint .            LINT_EXIT=0
  bunx vue-tsc --noEmit -> TSC_EXIT=0
  bun run test          -> $ vitest run
                           Test Files  19 passed (19)
                           Tests       209 passed (209)
                           TEST_EXIT=0
  ```
- Screenshots: n/a
- Test cases executed (see TESTPLAN.md): T1 PASS, T2 PASS, T3 PASS
- Self-check against acceptance criteria:
  1. No `web/frontend/**` file cites the deleted legacy tree/paths — PASS
     (both greps returned zero hits).
  2. New SPA entry `web/frontend/index.html` untouched; no legacy
     `index.html:<line>` citations remain — PASS.
  3. No runtime behaviour change (comments only) — PASS
     (lint/typecheck/test all green at baseline 209).
  4. Workspace artifacts recorded under `.agents/fe040-purge-implementer/` — PASS.

## Regression checks
- WS/clipboard/timer/token routing code bodies were not edited; only doc
  comments. `bun run test` (209) + `vue-tsc` confirm no behavioural drift.

## Kept as legitimate (not legacy tokens)
- `web/frontend/index.html` — the SPA's own Vite entry file (legitimate; not
  the deleted legacy `web/static/index.html`). A comment reference to it in
  `src/assets/styles/tokens.css:12` describes the inline theme bootstrap and is
  retained.
- `web/server.py:<line>` citations — `server.py` is not being deleted and is
  outside this purge's token set; retained as live backend contract references.
- `web/dist/` in `web/frontend/README.md` — generated build output, not a
  legacy token.

## Verifier — <different agent> (pending)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands: <commands and observed output>
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, ...>
- Criterion-by-criterion result: <...>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
