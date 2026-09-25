# EVIDENCE — FE-002

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — opencode (2026-09-10T06:02:32Z)
- Deliverable: design-token layer + base styles + dark/light theme switch.
- Files created:
  - `web/frontend/src/assets/styles/tokens.css` — slate+indigo palette (dark + light),
    radii, spacing, type, elevation, focus; `data-theme` selectors + no-JS
    `prefers-color-scheme` fallback.
  - `web/frontend/src/assets/styles/base.css` — reset + global element styles consuming
    tokens only.
  - `web/frontend/src/composables/useTheme.ts` — resolve/persist/apply theme
    (`localStorage` key `cka:theme`, `<html data-theme>`), OS-change listener.
  - `web/frontend/src/components/ThemeToggle.vue` — inline-SVG toggle button (no emoji,
    no hex).
  - `web/frontend/tests/unit/tokens.test.ts`, `tests/unit/hex-audit.test.ts`,
    `tests/unit/theme.test.ts`, `tests/unit/theme-toggle.test.ts`.
  - `web/frontend/tests/e2e/theme.spec.ts` — literal T2 Playwright spec (deferred, see below).
- Files modified:
  - `web/frontend/src/main.ts` — import tokens + base, call `initTheme()` before mount.
  - `web/frontend/src/App.vue` — minimal shell + `<ThemeToggle/>`.
  - `web/frontend/index.html` — removed hard-coded `data-theme="dark"`; added inline
    pre-paint theme bootstrap (prevents FOUC).
- Environment: Windows; Bun 1.4.2 (`node`/`npm`/`rg` absent); Python 3.12.4; no Playwright
  browser binaries, offline.

### Commands run + observed output
```
python scripts/agents_board.py --check
  [tasks] validation OK (44 tasks)

python scripts/agents_board.py --claim FE-002 opencode
  [tasks] FE-002 claimed by opencode
  [tasks] BOARD.md written (44 tasks: claimed=1, in-review=2, todo=41)

cd web/frontend
bun run test
  ✓ tests/unit/hex-audit.test.ts   (2 tests)
  ✓ tests/unit/tokens.test.ts      (27 tests)
  ✓ tests/unit/theme.test.ts       (7 tests)
  ✓ tests/unit/smoke.test.ts       (1 test)
  ✓ tests/unit/theme-toggle.test.ts(1 test)
  Test Files 5 passed (5) | Tests 38 passed (38)

bun run lint          -> eslint . ; exit 0
bunx tsc --noEmit     -> exit 0
bun run format:check  -> "All matched files use Prettier code style!"

bun run build
  vue-tsc --noEmit && vite build
  vite v6.4.3 building for production...
  ✓ 41 modules transformed.
  ../dist/index.html                  1.24 kB
  ../dist/assets/index-CJlwdHjK.css   6.38 kB   <- tokens.css + base.css bundled
  ../dist/assets/index-CDrd-3b6.js   94.43 kB
  ✓ built in 402ms

# T1 audit (rg unavailable -> equivalent scan; identical regex)
Get-ChildItem -Recurse src/components,src/views -Include *.vue,*.ts,*.css -File |
  Select-String -Pattern '#[0-9a-fA-F]{3,6}'
  -> NO_MATCHES: no raw hex in src/components or src/views

# Literal T2 browser e2e attempt
bunx playwright test tests/e2e/theme.spec.ts
  x [chromium] ... Error: launch: Executable doesn't exist at
    ...\ms-playwright\chromium_headless_shell-1243\...chrome-headless-shell.exe
  1 failed   <- DEFERRED: browser binary cannot be fetched offline
```

- Screenshots: n/a (headless environment).
- Test cases executed (see TESTPLAN.md): T1 PASS; T2 PASS-by-equivalent (jsdom
  integration + contrast); literal browser e2e DEFERRED.

### Self-check against acceptance criteria
1. **All palette values exposed as CSS variables; no raw hex in components — PASS.**
   `tokens.test.ts` asserts every PLAN.md §2 value exists as a variable in both themes;
   `hex-audit.test.ts` + the equivalent PowerShell scan find 0 hex literals under
   `src/components` and `src/views`.
2. **Dark and light themes both render with AA-contrast text — PASS (token level).**
   `tokens.test.ts` computes WCAG contrast for 11 text/background pairs per theme; all
   ≥ 4.5:1. `theme-toggle.test.ts`/`theme.test.ts` confirm both `data-theme` values apply.
   Full-page axe is deferred (no browser); the token math is the deterministic proof.
3. **`prefers-color-scheme` default + persisted manual toggle — PASS.**
   `theme.test.ts`: OS preference used when nothing stored; toggle writes `cka:theme` and
   flips `<html data-theme>`; a fresh module (simulated reload) honours the stored value
   over the OS preference; OS changes followed only without an override. `index.html`
   bootstrap applies it before first paint.

## Protocol notes
- FE-002 depends on FE-001, but FE-001 was `in-review` (not `verified`) at claim time.
  PROTOCOL §3 says dependencies should be `verified`; the explicit instruction to execute
  FE-002 was followed. `python scripts/agents_board.py --check` still passes because the
  validator does not enforce verified dependencies.
- An additional derived token, `--color-accent-text`, was added for AA-safe accent text on
  dark backgrounds; `--color-accent` retains the exact PLAN value.

## Verifier — verifier-1 (2026-09-10T06:09:10Z)

Independent re-run on the working tree of `feature/frontend-vue-migration`
(HEAD `e0fb4a3`; `web/frontend/` untracked). Environment: Windows, **Bun 1.4.2**,
no `node`/`npm`/`rg`, Python 3.12.4. I did not rely on any implementer output; all
numbers below are my own. Independent contrast math was recomputed from `tokens.css`
with a separate Python implementation (not the repo's Vitest code).

### Commands run + observed output (Verifier)
```
python scripts/agents_board.py --check  -> "[tasks] validation OK (44 tasks)"  exit 0

# T1 hex audit (rg absent -> equivalent Select-String, same regex)
Get-ChildItem -Recurse src/components,src/views -Include *.vue,*.ts,*.css |
  Select-String -Pattern '#[0-9a-fA-F]{3,6}'
  -> NO_MATCHES
Get-ChildItem -Recurse src -Include *.vue,*.ts,*.css |
  Select-String -Pattern '#[0-9a-fA-F]{3,6}'
  -> matches ONLY in src/assets/styles/tokens.css (the token layer), e.g. lines 21-202

# independent WCAG contrast recomputation (Python, parses tokens.css)
DARK  11/11 pairs PASS (>=4.5): text/bg 15.78, text/surface 14.58, muted/bg 7.61,
      muted/surface 7.03, accent-text/surface 8.89, accent-text/bg 9.63,
      accent-contrast/accent-solid 6.29, success 10.18, warning 10.62, danger 6.41, info 9.83
LIGHT 11/11 pairs PASS (>=4.5): text/bg 16.65, text/surface 17.85, muted/bg 5.44,
      muted/surface 5.83, accent-text/surface 6.29, accent-text/bg 5.87,
      accent-contrast/accent-solid 6.29, success 5.02, warning 5.02, danger 6.47, info 5.17
media-fallback block vs light block: 26 vs 26 decls, differences: NONE (identical)
dark palette vs PLAN.md §2: mismatches NONE
light palette vs PLAN.md §2: mismatches NONE
TOTAL CONTRAST FAILURES: 0

bun run test  -> 5 files / 38 tests passed (tokens 27, theme 7, hex-audit 2, toggle 1, smoke 1)  exit 0
bun run build -> ../dist/assets/index-CJlwdHjK.css 6.38 kB (tokens+base bundled), index-CDrd-3b6.js  exit 0
bun run lint  -> exit 0 ; bunx tsc --noEmit -> exit 0 ; bun run format:check -> clean

# literal browser e2e (implementer claimed DEFERRED; it actually runs and PASSES here)
bunx playwright test
  ok [chromium] FE-002 T2: theme toggle flips, persists across reload and stays AA
  ok [chromium] candidate route renders the app shell
  ok [chromium] admin route renders the app shell
  3 passed (753ms)  exit 0
  browser cache present: chromium-1243, chromium_headless_shell-1243, firefox-1543, webkit-2359
```

### Acceptance criterion results (Verifier)
1. **All palette values exposed as CSS variables; no raw hex in components/views — PASS.**
   `tokens.css` declares the full dark + light palette; my independent scan of
   `src/components` and `src/views` returns 0 matches, and the whole-`src` scan confines
   every hex literal to `tokens.css`. Dark and light values match PLAN.md §2 exactly
   (independent comparison: no mismatches).
2. **Dark and light themes both render AA-contrast text — PASS.** 22/22 text pairs
   (11 per theme) recomputed independently at >= 4.5:1 (lowest 5.02). The literal browser
   spec also measures computed `body` fg/bg contrast in both states and passes. Note (as
   documented): `--color-text-dim` is decorative-only and intentionally not used for body text.
3. **`prefers-color-scheme` default + persisted manual toggle — PASS.** `index.html`
   pre-paint bootstrap + `useTheme.ts` (`cka:theme`) + `ThemeToggle.vue`; the literal
   Playwright spec asserts the toggle flips `data-theme`, **survives `page.reload()`**, and
   both states stay AA. Unit suites independently cover OS-default, reload persistence,
   OS-change handling and clear-to-OS.

### Regression / adjacent-behavior checks
- a11y/contrast: checked (above). WS, clipboard, timer, anti-cheat, replay: **n/a** — this
  task only adds tokens/base styles + a theme toggle; none of those subsystems exist yet in
  the scaffold, and no legacy `web/static` code is imported, so no parity surface changed.
- Build hygiene: `web/dist` is git-ignored (D-005); `node_modules`/`bun.lock` ignored.

### Discrepancies vs implementer claims (for the record)
- Implementer reported the browser leg as **DEFERRED** ("chromium binary absent, offline").
  In this verifier environment the Playwright browsers ARE installed and the literal
  `tests/e2e/theme.spec.ts` (plus `smoke.spec.ts`) **PASS**. No browser deferral is needed.
- Minor tooling gap: `playwright.config.ts` `webServer.command` is `npm run dev`; on a
  Bun-only host the config cannot auto-start the server (fails with "'npm' is not
  recognized"). Pre-starting `bun run dev` (which the config reuses) lets the suite run.
  Not a task defect (canonical host has npm) but worth noting for local runs.
- `playwright test` without a running server cannot be used verbatim here for the same
  reason; the platform host (npm) is unaffected.

### Verdict: `verified` (accepted)
T1 and T2 both PASS with my own evidence, including the literal browser e2e. All three
acceptance criteria met; zero contrast failures; no regressions.
