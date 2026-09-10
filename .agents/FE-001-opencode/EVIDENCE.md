# EVIDENCE — FE-001

## Implementer — opencode (2026-09-10)
- Deliverable: `web/frontend/` Vite + Vue 3 + TS scaffold with ESLint/Prettier,
  Vitest, Playwright, dev proxy, build output to `web/dist/`.
- Files touched:
  - `web/frontend/package.json`, `vite.config.ts`, `vitest.config.ts`, `tsconfig.json`
  - `web/frontend/index.html`, `env.d.ts`, `eslint.config.js`
  - `web/frontend/.prettierrc.json`, `.prettierignore`, `.gitignore`, `playwright.config.ts`, `README.md`
  - `web/frontend/src/{main.ts,App.vue}`, `src/router/index.ts`
  - `web/frontend/src/views/{CandidateView,AdminView,PlaceholderView}.vue`
  - `web/frontend/tests/unit/smoke.test.ts`, `tests/e2e/smoke.spec.ts`
  - `.gitignore` (root) — ignores `web/dist/` and frontend build artifacts
- Environment: Node/npm not on PATH; **Bun 1.4.2** used for install/build/test.
- Commands run + output:
  ```
  bun install                 -> 303 packages installed; lockfile saved
  bun run build               -> vue-tsc --noEmit OK; vite v6.4.3 built 33 modules in 646ms
                                 ../dist/index.html 0.41 kB
                                 ../dist/assets/index-DVgSmIMI.js 91.98 kB
                                 ../dist/assets/PlaceholderView-D0bCX6VM.js 0.41 kB
  bun run lint                -> eslint . (clean, exit 0)
  bunx tsc --noEmit           -> exit 0
  bun run test                -> vitest v3.2.7: 1 test passed
  bun run format:check        -> All matched files use Prettier code style
  ```
- Screenshots: n/a (blank scaffold)
- Test cases executed: T1 PASS, T2 PASS, T3 PASS (see TESTPLAN.md)
- Deviations:
  - Upgraded `vitest` `^2.1.8` -> `^3.2.4`: Vitest 2.x bundled a nested Vite copy that
    broke `vue-tsc` plugin typing against root Vite 6.
  - `bun.lock` ignored (npm is the canonical package manager; host generates
    `package-lock.json`).
- Self-check against acceptance criteria:
  1. `npm run build` emits `web/dist` — PASS (via Bun; npm pending on host)
  2. dev proxy reaches FastAPI — DEFERRED (backend only runs on platform host)
  3. ESLint + Prettier + tsc — PASS
  4. Vitest smoke — PASS

## Verifier — verifier-1 (2026-09-10T06:09:10Z)

Independent re-run on the working tree of `feature/frontend-vue-migration`
(HEAD `e0fb4a3`). The `web/frontend/` deliverable is **untracked/uncommitted**, so a
literal "clean checkout" cannot include it; I verified the present working tree and
verified that the deliverable is self-contained (no reliance on modified tracked files).
The implementer was not consulted; every result below is my own observation.

- Environment: Windows; **Bun 1.4.2**; `node`/`npm`/`rg` **absent** (confirmed:
  `node --version`/`npm --version`/`rg --version` all "not recognized"); Python 3.12.4.
- Preconditions: `python scripts/agents_board.py --check` -> `[tasks] validation OK (44 tasks)`
  (exit 0). `web/frontend/node_modules` present; **removed `web/dist` before building** so
  emission could not be a stale artifact.

### Commands run + observed output (Verifier)
```
bun install
  -> "Checked 314 installs across 355 packages (no changes) [45.00ms]"  exit 0

Remove-Item web/dist ; bun run build
  -> vue-tsc --noEmit OK; vite v6.4.3 building for production...
     ✓ 41 modules transformed.
     ../dist/index.html                  1.24 kB
     ../dist/assets/index-CJlwdHjK.css    6.38 kB
     ../dist/assets/index-CDrd-3b6.js    94.43 kB
     ../dist/assets/PlaceholderView-*.js  0.41 kB
     ✓ built in 413ms   exit 0
  -> web/dist/index.html exists = True (was absent before build)

bun run lint          -> eslint . (no output)                       exit 0
bunx tsc --noEmit     -> (no output)                                exit 0
bun run format:check  -> "All matched files use Prettier code style!" exit 0

bun run test          -> vitest v3.2.7
  ✓ tests/unit/hex-audit.test.ts      (2 tests)
  ✓ tests/unit/tokens.test.ts         (27 tests)
  ✓ tests/unit/theme.test.ts          (7 tests)
  ✓ tests/unit/smoke.test.ts          (1 test)
  ✓ tests/unit/theme-toggle.test.ts   (1 test)
  Test Files 5 passed (5) | Tests 38 passed (38)   exit 0

# dev server + proxy (acceptance #2)
bun run dev           -> VITE v6.4.3 ready in 200 ms; http://localhost:5173/
GET http://localhost:5173/            -> 200; body contains id="app"
GET http://localhost:5173/api/session -> 500 (Vite http proxy error: ECONNREFUSED to
                                         http://localhost:3000) => proxy IS wired, backend absent

# literal browser e2e (implementer reported this as blocked; it is NOT)
bunx playwright test
  Running 3 tests using 3 workers
  ok 1 [chromium] candidate route renders the app shell
  ok 2 [chromium] admin route renders the app shell
  ok 3 [chromium] FE-002 T2: theme toggle flips, persists across reload and stays AA
  3 passed (753ms)   exit 0
  (browser cache present: chromium-1243, chromium_headless_shell-1243, firefox-1543, webkit-2359)
```

### Acceptance criterion results (Verifier)
1. **build succeeds and emits `web/dist/` — PASS.** Removed `web/dist` first; build exit 0
   and emitted `web/dist/index.html` + `assets/` (observed, not stale).
2. **dev starts and `/api` proxy reaches FastAPI on :3000 — PASS (config + boot), backend
   reachability HOST-ONLY.** `bun run dev` boots and serves `/` (200). Proxy config in
   `vite.config.ts` maps `/api`, `/ws`, `/novnc` -> `VITE_BACKEND` (default
   `http://localhost:3000`); the live `/api` call exercised the proxy path and failed only
   with ECONNREFUSED because no FastAPI is running here. Actual FastAPI reachability must
   be re-run on the platform host (noted as host-only).
3. **ESLint + Prettier + `tsc --noEmit` pass — PASS.** `bun run lint` exit 0;
   `bunx tsc --noEmit` exit 0; `bun run format:check` clean.
4. **Vitest smoke test passes — PASS.** 5 files / 38 tests green including
   `tests/unit/smoke.test.ts`.

### Regression / adjacent-behavior checks
- WS, clipboard, timer, anti-cheat, replay: **n/a** — FE-001 is a blank scaffold and
  intentionally implements none of these (deliverable note: "Do not migrate UI yet; blank
  app only"). No legacy `web/static` behaviour is wired into the new SPA, so no parity
  surface is changed by this task.
- Build hygiene: `git check-ignore web/dist/index.html` -> `.gitignore:11:web/dist/` (D-005
  honoured); `node_modules` ignored by `web/frontend/.gitignore`; `bun.lock` ignored.

### Verdict: `verified` (accepted)
All four acceptance criteria met; T1/T2/T3 PASS. The only non-local item is live FastAPI
reachability behind the dev proxy (host-only). The implementer's claim that Playwright
browsers are absent does **not** hold in this environment — the literal browser suite
passes (see FE-002 evidence), so no browser deferral is carried.
