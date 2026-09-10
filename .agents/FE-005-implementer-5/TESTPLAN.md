# TESTPLAN — FE-005

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-005` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run build && bun run lint && bunx tsc --noEmit && bun run test` | all pass; Tailwind plugin active in the build | **PASS** — build 117 modules (was 54), dist CSS 18.29 kB, Tailwind v4.3.3 banner + preflight/utilities present; lint/tsc exit 0; Vitest 7 files / 62 tests passed | **PASS** (verifier-5) — build exit 0, 117 modules, CSS 18.29 kB; lint exit 0; `tsc --noEmit` exit 0; Vitest 7 files / 62 tests passed (tokens 27, hex-audit 2, theme 7, theme-toggle 1, smoke 1, stores 10, toast 14) |
| T2 | audit | confirm `tailwindcss` + `@tailwindcss/vite` + `@headlessui/vue` installed; no CDN/external URLs in `src` or `index.html` | deps present; no external asset URLs | **PASS** — `tailwindcss@4.3.3`, `@tailwindcss/vite@4.3.3`, `@headlessui/vue@1.7.23`; 0 external URL matches in `src/**` and `index.html` | **PASS** (verifier-5) — installed versions 4.3.3/4.3.3/1.7.23 confirmed from `node_modules`; Vite plugin wired; `@import 'tailwindcss'` + `@theme inline` present; `@headlessui/vue` bundled (`headlessui` in dist JS); grep `https?://`/`@import url(` over `src/**` = 0, `index.html` clean |
| T3 | integration | Playwright toast spec + hex audit over `src/components` and `src/views` | axe 0 violations; 0 raw hex; both themes AA | **PASS** — `tests/e2e/toast.spec.ts` 1 passed (axe violations `[]`); `tests/e2e/theme.spec.ts` 1 passed (both themes ≥ 4.5:1); `hex-audit.test.ts` 2 passed | **PASS** (verifier-5) — fresh-server `bunx playwright test` 4 passed incl. toast axe `violations === []`; `hex-audit.test.ts` 2 passed; hex grep over `src/components`+`src/views` = 0. Temporary cascade probe (deleted) read computed toast colours in dark+light and all matched `tokens.css` exactly |

## Edge cases / additions
- **FE-002 regression:** `tests/unit/tokens.test.ts` — 27 passed (exact token values + AA for dark/light).
- **FE-002 regression:** `tests/unit/hex-audit.test.ts` — 2 passed (0 raw hex in `src/components` + `src/views`).
- **FE-002 regression:** `tests/e2e/theme.spec.ts` — 1 passed (toggle flips, persists, AA in browser).
- **FE-010 regression:** `tests/unit/toast.test.ts` — 14 passed (4 variants, stacking, auto-dismiss, pause/resume, aria-live, class hooks).
- **FE-010 regression:** `tests/e2e/toast.spec.ts` — 1 passed (4 variants, `role=alert` for error, manual dismiss, axe WCAG 2 A/AA 0 violations).
- **Token mapping:** built CSS confirms utilities resolve to runtime token vars, e.g.
  `.bg-elevated{background-color:var(--color-elevated)}`,
  `.text-text{color:var(--color-text)}`,
  `.border-l-info-text{border-left-color:var(--color-info-text)}`,
  `.rounded-[var(--radius-md)]{border-radius:var(--radius-md)}`.
  Tailwind re-emits theme vars inside `@layer theme`; `tokens.css` is unlayered so its
  values win the cascade (verified by the browser axe/AA tests computing correct colours).
- **External assets:** 0 (`grep`), so no CDN dependency introduced.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (no commits made)
- Host: Windows 11, Bun 1.4.2, Node v26.8.2, npm 11.19.1, Python 3.12.4
- Browser(s): Chromium (Playwright 1.63.0, `chromium-1243`)

## Verdict
- Implementer: **PASS** (2026-09-10T08:32Z)
- Verifier: **PASS** — verifier-5 (2026-09-10T08:44:13Z). All T1–T3 re-run green; cascade independently proven against `tokens.css` in dark+light; no regressions; no out-of-scope edits or deletions attributable to FE-005.
