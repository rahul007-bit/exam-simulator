# EVIDENCE — FE-005

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-5 (2026-09-10T08:28:53Z)

### Deliverable
Adopt **Tailwind CSS v4** (`@tailwindcss/vite`) + **`@headlessui/vue`**, expose the
existing `tokens.css` palette to Tailwind via `@theme inline`, and refactor the
foundation stylesheet and the Toaster onto the new stack — preserving FE-002 and
FE-010 acceptance.

### Deps added
| Package | Version | Kind |
| :--- | :--- | :--- |
| `tailwindcss` | `4.3.3` | devDependency |
| `@tailwindcss/vite` | `4.3.3` | devDependency |
| `@headlessui/vue` | `1.7.23` | dependency |

### Files touched
| File | Change |
| :--- | :--- |
| `web/frontend/package.json` | + `tailwindcss`, `@tailwindcss/vite` (dev), `@headlessui/vue` (prod) |
| `web/frontend/vite.config.ts` | `import tailwindcss from '@tailwindcss/vite'`; `plugins: [vue(), tailwindcss()]` |
| `web/frontend/src/assets/styles/base.css` | `@import 'tailwindcss';` + `@theme inline { --color-*: var(--color-*) }`; existing base rules moved into `@layer base`, helpers into `@layer components` |
| `web/frontend/src/components/Toaster.vue` | refactored to Tailwind utilities + `@headlessui/vue` `TransitionRoot`; scoped `<style>` block removed |
| `.agents/FE-005-implementer-5/*` | task workspace metadata |
| `.agents/frontend-migration/{tasks.json,BOARD.md}` | updated via `scripts/agents_board.py` only |

`tokens.css` was **not modified** — it remains the palette source of truth
(verified by the unchanged `tokens.test.ts`, 27 passed).

### Config summary
- **Vite plugin:** `plugins: [vue(), tailwindcss()]` (Tailwind v4 Vite plugin).
- **Single import:** `@import 'tailwindcss';` at the top of `base.css` (imported once
  from `src/main.ts`).
- **Token mapping (`@theme inline`):** `--color-app: var(--color-bg-app)`,
  `--color-surface`, `--color-elevated`, `--color-hover`, `--color-border`,
  `--color-border-strong`, `--color-text`, `--color-text-muted`, `--color-text-dim`,
  the `--color-accent*` family, and the semantic `--color-{success,warning,danger,info}`
  + `--color-*-text` AA variants. `inline` makes the generated utilities reference the
  runtime `var(--color-*)` values, so `data-theme` dark/light keeps working.

### Behaviour preserved (FE-010)
- All class hooks kept alongside Tailwind utilities: `.toaster`, `.toaster__list`
  (`[aria-live="polite"]`), `.toast`, `.toast--info|success|warning|error`,
  `.toast__close`, `.toast__content`, `.toast__title`, `.toast__message`, `.toast__icon`.
- `role="alert"` for `error`, `role="status"` otherwise; persistent polite live region;
  labelled close button; hover/focus pause + resume. Behaviour is identical; only the
  styling mechanism changed.
- The scoped `toast-in` keyframes are replaced by a Headless UI `TransitionRoot`
  (`appear`, `enter`/`enter-from`/`enter-to`) — an accessible primitive. Enter-only, to
  match the original animation and keep dismiss lifecycle/tests unchanged.

### Commands run + observed output (cwd `web/frontend/`)
```
bun add -d tailwindcss @tailwindcss/vite
  -> installed tailwindcss@4.3.3, @tailwindcss/vite@4.3.3
bun add @headlessui/vue
  -> installed @headlessui/vue@1.7.23

bun run build
  -> $ node scripts/gen-api.mjs && vue-tsc --noEmit && vite build
  -> ✓ 117 modules transformed.
  -> ../dist/index.html 1.24 kB
     ../dist/assets/index-iB36U86J.css 18.29 kB │ gzip 4.56 kB
     ../dist/assets/index-CneGMHTI.js 121.48 kB │ gzip 46.05 kB
  -> ✓ built in 1.43s                                        BUILD_EXIT=0

bun run lint
  -> $ eslint .                                              LINT_EXIT=0

bunx tsc --noEmit
  -> (no errors)                                             TSC_EXIT=0

bun run test
  -> ✓ tests/unit/hex-audit.test.ts (2 tests)
     ✓ tests/unit/tokens.test.ts (27 tests)
     ✓ tests/unit/theme.test.ts (7 tests)
     ✓ tests/unit/theme-toggle.test.ts (1 test)
     ✓ tests/unit/smoke.test.ts (1 test)
     ✓ tests/unit/stores.test.ts (10 tests)
     ✓ tests/unit/toast.test.ts (14 tests)
  -> Test Files 7 passed (7) | Tests 62 passed (62)          TEST_EXIT=0

bunx playwright test tests/e2e/toast.spec.ts
  -> ok 1 [chromium] FE-010 toasts render, are announced, dismiss, and pass axe
  -> 1 passed (1.6s)                                         PLAYWRIGHT_TOAST_EXIT=0

bunx playwright test            # full suite (smoke + theme + toast)
  -> 4 passed (2.0s)                                         PLAYWRIGHT_EXIT=0
```

### Evidence that the Tailwind plugin is active (T1)
Built CSS (`web/dist/assets/index-iB36U86J.css`) contains the Tailwind v4.3.3 banner,
preflight, and the generated utilities. Spot checks (raw strings from the bundle):
```
.text-text{color:var(--color-text)}
.text-text-muted{color:var(--color-text-muted)}
.bg-elevated{background-color:var(--color-elevated)}
.border-border{border-color:var(--color-border)}
.border-l-info-text{border-left-color:var(--color-info-text)}
.border-l-success-text{border-left-color:var(--color-success-text)}
.border-l-warning-text{border-left-color:var(--color-warning-text)}
.border-l-danger-text{border-left-color:var(--color-danger-text)}
.hover\:bg-hover:hover{background-color:var(--color-hover)}
.rounded-\[var\(--radius-md\)\]{border-radius:var(--radius-md)}
.shadow-\[var\(--shadow-md\)\]{--tw-shadow:var(--shadow-md);box-shadow:...}
.z-\[1000\]{z-index:1000}
.pointer-events-none{pointer-events:none}
.motion-reduce\:transition-none{transition-property:none}
```
Every utility resolves to a `tokens.css` variable; no literal colours. The module count
rose 54 → 117 (Headless UI + Tailwind runtime modules bundled).

### Test cases executed (see TESTPLAN.md)
**T1 PASS** — build/lint/tsc/test all exit 0; Tailwind active (banner + generated utilities).
**T2 PASS** — deps present (`tailwindcss@4.3.3`, `@tailwindcss/vite@4.3.3`,
`@headlessui/vue@1.7.23`); `grep`/`Select-String` for external URLs over `src/**` and
`index.html` → 0 matches.
**T3 PASS** — `tests/e2e/toast.spec.ts` 1 passed with axe `violations === []`;
`tests/e2e/theme.spec.ts` 1 passed (body contrast ≥ 4.5:1 in both themes);
`tests/unit/hex-audit.test.ts` 2 passed (0 raw hex in `src/components` + `src/views`).

### FE-002 / FE-010 re-verification (no regressions)
- FE-002: `tokens.test.ts` 27 passed (exact palette values + AA); `hex-audit.test.ts`
  2 passed; `theme.spec.ts` 1 passed (browser contrast both themes).
- FE-010: `toast.test.ts` 14 passed; `toast.spec.ts` 1 passed (browser axe 0).

### Screenshots
n/a — all legs ran headless on this host; Playwright Chromium was available so the
browser legs are **not** deferred here.

### Self-check against acceptance criteria
1. **Tailwind + Headless UI installed and wired into the Vite build — PASS.** Deps in
   `package.json`; `tailwindcss()` in `vite.config.ts`; build emits Tailwind output;
   `TransitionRoot` imported from `@headlessui/vue`.
2. **Design tokens exposed to Tailwind (`@theme`) so utilities resolve to the token
   palette; no raw hex in components/views — PASS.** `@theme inline` mapping in
   `base.css`; built utilities reference `var(--color-*)`; `hex-audit` clean.
3. **`@headlessui/vue` used for at least one accessible primitive — PASS.** Toaster
   enter transition via `TransitionRoot` (`appear` + enter classes).
4. **FE-002 (dark/light AA, no raw hex) + FE-010 (4 variants, aria-live, axe 0) still
   pass — PASS.** All listed tests re-ran green, including the literal browser axe run.

### Safety / scope
- No destructive git commands; nothing committed/amended/pushed/PR'd.
- FE-005-scoped files only (see table). `web/frontend/` is an untracked tree on this
  branch; the only build side effect is regeneration of `src/api/schema.d.ts` by the
  existing `gen:api` step (unchanged content, FE-004-owned).
- `tasks.json` / `BOARD.md` updated only through `scripts/agents_board.py`.
- Status set to `in-review` only; **not** marked `verified` (independent verifier required).

## Verifier — verifier-5 (independent, 2026-09-10T08:44:13Z)

I did **not** implement FE-005. I re-derived every result below on the branch as
checked out (no commits, no source edits).

### Environment
- Windows 11, Bun 1.4.2, Node v26.8.2, npm 11.19.1, Python 3.12.4.
- Browser: Chromium via Playwright. The browser legs ran against a **fresh**
  `npm run dev` managed by Playwright's `webServer` (a stale pre-Tailwind
  `bun run dev` was found squatting on :5173 and killed first — see Concerns).

### Commands re-run + observed output (cwd `web/frontend/`)
```
bun run build
  -> gen:api + vue-tsc --noEmit + vite build
  -> ✓ 117 modules transformed; dist/css 18.29 kB │ gzip 4.56 kB; dist/js 121.48 kB
  -> ✓ built in 1.47s                                          BUILD_EXIT=0
bun run lint            -> eslint . (no findings)              LINT_EXIT=0
bunx tsc --noEmit       -> (no errors)                         TSC_EXIT=0
bun run test            -> 7 files / 62 tests passed           TEST_EXIT=0
   tokens 27 · hex-audit 2 · theme 7 · theme-toggle 1 · smoke 1 · stores 10 · toast 14
bunx playwright test    -> 4 passed (smoke×2, theme 1, toast axe 1)   PLAYWRIGHT_EXIT=0
```

### Cascade correctness — INDEPENDENT PROBE (temporary, deleted)
Wrote `tests/e2e/_fe005-cascade-probe.spec.ts` (temporary; removed after the run,
`Test-Path` -> False). It renders all four toast variants, sets `data-theme=dark`
then `light` on `<html>`, settles 400 ms, and reads **computed** styles and the
resolved custom properties. Result: **PASS**, every value equals `tokens.css`.

```
[cascade dark]  toast bg rgb(26, 34, 51)=#1a2233
                border info/success/warning/error =
                  rgb(147,197,253) / rgb(74,222,128) / rgb(251,191,36) / rgb(248,113,113)
                text rgb(230,233,239)=#e6e9ef
                resolved vars: --color-elevated #1a2233; --color-*-text
                  #93c5fd / #4ade80 / #fbbf24 / #f87171
[cascade light] toast bg rgb(255,255,255)=#ffffff
                border info/success/warning/error =
                  rgb(37,99,235) / rgb(21,128,61) / rgb(180,83,9) / rgb(185,28,28)
                text rgb(15,23,42)=#0f172a
                resolved vars: --color-elevated #ffffff; --color-*-text
                  #2563eb / #15803d / #b45309 / #b91c1c
```

Conclusion: Tailwind utilities (`.bg-elevated`, `.border-l-*-text`, `.text-text`)
resolve to the **unlayered** `tokens.css` values in both themes. Tailwind's
`@layer theme` re-emission does **not** win the cascade (unlayered normal
declarations outrank layered ones) and the `@theme inline` self-referential
declarations are harmless. **No cascade defect.**

Method note: my *first* probe read immediately after flipping `data-theme`
(no settle) and produced a mixed dark-text/light-border reading. Adding a 400 ms
settle made every value consistent and correct — a probe timing artifact, not an
application bug. The initial run also hit a stale dev server (below).

### Acceptance criteria — confirmed with evidence
1. **Installed + wired** — `tailwindcss@4.3.3` + `@tailwindcss/vite@4.3.3` (dev),
   `@headlessui/vue@1.7.23` (prod); `vite.config.ts` `plugins: [vue(), tailwindcss()]`;
   `base.css` `@import 'tailwindcss'` + `@theme inline`; built CSS carries the
   Tailwind v4.3.3 banner and generated `.text-text{color:var(--color-text)}` etc. **PASS**
2. **Tokens → Tailwind, no raw hex** — built utilities reference `var(--color-*)`
   (0 literal colours); grep `#[0-9a-fA-F]{3,6}\b` over `src/components` +
   `src/views` = **0 matches**; `hex-audit.test.ts` 2 passed. **PASS**
3. **Headless UI primitive** — `Toaster.vue` imports/uses `TransitionRoot`; built
   bundle contains the `headlessui`/`Transition` runtime. **PASS**
4. **FE-002 + FE-010 preserved** — tokens 27, hex-audit 2, theme 7, theme-toggle 1,
   toast 14 all passed; Playwright toast axe `violations === []` (**0**); theme spec
   AA in both themes. **PASS**

### Class hooks / a11y preserved
`.toaster`, `.toaster__list` with `aria-live="polite"`, `.toast`,
`.toast--{info,success,warning,error}`, `.toast__close`, `.toast__content/__title/
__message/__icon`; `role="alert"` for error, `role="status"` otherwise; labelled
close button; hover/focus pause-resume. Confirmed in source and in the Playwright run.

### External assets
0 matches for `https?://` / `@import url(` under `src/**`; `index.html` contains no
external/CDN URLs (only the inline theme bootstrap and `/src/main.ts`). **PASS**

### Scope / git
- **No deletions** (`git status` shows only ` M` tracked edits and `??` untracked; no `D`).
- The 11 modified tracked files are pre-existing backend/legacy work outside FE-005
  scope (`.gitignore`, `PLATFORM_SETUP.md`, `core/*`, `docker/*`, `tools/*`,
  `web/server.py`, `web/static/*`). FE-005 touches only `web/frontend/` (an untracked
  tree); I found no FE-005-driven edit to those files.
- `bun run build` regenerated the git-ignored `src/api/schema.d.ts` (FE-004-owned) —
  expected (`git check-ignore` confirms it is ignored).
- Nothing committed, amended, pushed, or PR'd; no destructive git commands.

### Concerns / host-only items
- **Stale dev server (operational):** a long-running `bun run dev` (started 13:47:56)
  predated the final Tailwind edits (`vite.config.ts` 13:54, `base.css` 13:54,
  `Toaster.vue` 13:57) and served **uncompiled** Tailwind (`@tailwind utilities;`
  literal, no utilities). Playwright `reuseExistingServer` silently reused it. A fresh
  server compiles correctly; all results above use a fresh server. Not an FE-005
  defect, but worth a restart on the host after config changes.
- No browser legs deferred — Chromium was available and the literal suites ran.

### Verdict: **PASS** — FE-005 verified and accepted.
