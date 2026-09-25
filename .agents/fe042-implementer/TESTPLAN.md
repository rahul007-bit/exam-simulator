# TESTPLAN — FE-042

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-042` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | `npx playwright test` (host-only; requires `npx playwright install`) | all journeys pass | **PASS (fix pass)** — `npx playwright test --reporter=list` → **20 passed / 0 failed** (4.3s). Verified locally on the host. | <pending> |
| T2 | audit | `npx playwright test tests/e2e/a11y.spec.ts` (browser, host-only) | no critical violations | **PASS (fix pass)** — both axe specs reach the scan; **0 critical** WCAG 2 A/AA violations on candidate start screen, preset modal, `/admin` and session-actions dialog. | <pending> |

## Edge cases / additions
- Candidate: asserts the start screen, active workspace/header, question-drawer
  modal, task jump via `/api/action/jump`, and the submit confirm → scorecard.
- Admin: asserts the sessions table, default-preset + resource forms, the
  row-action dialog (terminate + confirm) and the create-invite flow.
- Axe: scans `/` (start screen), the open preset modal, `/admin`, and the open
  session-actions dialog; filters by `impact === 'critical'` and prints the
  offending nodes on failure.
- Offline determinism: `window.WebSocket` is stubbed (never connects),
  `requestFullscreen` is simulated as a successful fullscreen round-trip (so the
  candidate `FullscreenGuard` overlay never blocks clicks), and `/novnc/**`
  returns a stub document.
- Route scoping: the mock dispatcher matches `/^https?:\/\/[^/]+\/api\//`, not
  `**/api/**`, so it never intercepts Vite dev modules under `/src/api/*.ts`.

## Environment
- Commit / build: `79297c8` (branch `feature/frontend-vue-migration`)
- Host: win32 (Bun on PATH), project `C:/Users/HP/Projects/4-sep-test/cka-labs`
- Browser(s): Playwright Chromium (headless, via `playwright.config.ts`)

## Verdict
- Implementer: **PASS (fix pass, local)** — `npx playwright test` → 20 passed /
  0 failed; `bunx vue-tsc --noEmit` and `bun run lint` pass. No `src/**` change.
- Verifier: <PASS/FAIL, timestamp, reasons if FAIL>
