# TESTPLAN — FE-040 (purge part 1)

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | audit | `git grep -nE 'web/static\|static/js\|static/css\|app\.js\|admin\.js\|admin\.html\|style\.css' -- web/frontend` (from repo root) | zero hits | PASS | |
| T2 | audit | `git grep -nE 'app\.js:[0-9]+\|admin\.js:[0-9]+\|index\.html:[0-9]+' -- web/frontend` | zero hits | PASS | |
| T3 | unit/integration | `bun run lint && bunx vue-tsc --noEmit && bun run test` (from `web/frontend/`) | all exit 0; 209 tests pass | PASS (lint 0, tsc 0, 209/209) | |

## Edge cases / additions
- `web/frontend/index.html` is the SPA entry — asserted it still exists and is
  not treated as a legacy token.
- `web/server.py:<line>` and `web/dist/` references judged legitimate, kept.

## Environment
- Commit / build: `47471ad` (working tree changes, no commit)
- Host: Windows / branch `feature/frontend-vue-migration`
- Browser(s): n/a (no build/Playwright run per instructions)

## Verdict
- Implementer: PASS, 2026-09-10T18:07:23Z
- Verifier: pending
