# TESTPLAN — FE-011

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-011` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run test` → `tests/unit/confirm.test.ts` (8 tests) | confirm→true, cancel→false, prompt→value, prompt cancel→null | **PASS** — 8/8: confirm true; cancel false; `Escape` false; prompt returns typed value; prompt cancel `null`; FIFO queue; aria wiring; initial focus on confirm. Full suite 8 files / 70 tests pass. | **PASS (re-run)** — `bun run test` 8 files / 70 tests. Plus my own `zz-verifier-probe.test.ts` (8 independent tests, deleted): confirm→true, cancel→false, prompt→value, empty→`''`, cancel→`null`, FIFO settlement order, empty-queue no-op, defaults. |
| T2 | e2e | `npx playwright test tests/e2e/confirm.spec.ts` (Chromium) | keyboard-only: Escape cancels, Tab/Shift+Tab trapped, `aria-modal="true"`, confirm focused | **PASS** — 2/2 real-browser tests. Full e2e suite 6/6 pass (smoke, theme, toast, confirm). | **PASS (re-run)** — full `npx playwright test` 6/6. Plus my own `zz-verifier-probe.spec.ts` (4 independent Chromium tests, deleted): role/aria-modal/labelledby/describedby, initial focus (confirm + prompt input), Tab/Shift+Tab trap, Escape cancel, focus return to invoker, prompt value/null, FIFO live, axe 0 on open dialog. |

## Edge cases / additions
- E1 — **Concurrency**: two requests issued while one is open resolve in FIFO
  order; the second renders only after the first settles. PASS (unit).
- E2 — **Default value**: prompt pre-fills `defaultValue`; empty submit resolves
  `''` (not `null`). PASS (unit).
- E3 — **aria labelling**: `role="dialog"`, `aria-modal="true"`,
  `aria-labelledby` → title element, `aria-describedby` → description element.
  PASS (unit).
- E4 — **Focus return**: after `Escape`, focus returns to the element focused
  before the dialog opened. PASS (e2e).
- E5 — **Queue remount**: switching between queued dialogs re-runs initial
  focus (input for prompt, confirm button for confirm). PASS (unit + e2e).
- E6 — **Constraints**: no raw hex, no `text-shadow`/`drop-shadow`/`blur(` and no
  emoji/non-ASCII glyphs in the new source; `hex-audit` still passes. PASS.

## Environment
- Commit / build: working tree (no commits), branch `feature/frontend-vue-migration`
- Host: Windows, Bun 1.4.2, Node v26.8.2, Playwright 1.63.0 (Chromium 1243)
- Browser(s): Chromium (headless) via Playwright `webServer` = `npm run dev`

## Verdict
- Implementer: **PASS**, 2026-09-10T08:58:37Z
- Verifier: **PASS**, verifier-7, 2026-09-10T09:03:13Z — independently re-ran all commands and wrote separate unit + browser probes; all criteria reproduced; axe 0; no regressions. Advisory cleanup: remove stray `web/frontend/hex`.
