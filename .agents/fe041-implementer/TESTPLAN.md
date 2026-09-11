# TESTPLAN - FE-041

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-041` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit/audit | `bun run test` (`tests/unit/offline-audit.test.ts`) | No external font/CDN domains in `src/**` + `index.html`; `@font-face` for `Inter` + `JetBrains Mono` use `/fonts/`; referenced woff2 exist and are valid `wOF2` | PASS (9 tests) | <pending> |
| T2 | manual | Serve build/offline, inspect network + render | No external requests; styled + functional offline | DEFERRED (no browser/build in this environment) | <pending> |

## Edge cases / additions
- T1 also asserts `base.css` imports `fonts.css` *after* the tailwind import.
- T1 also asserts every shipped `.woff2` is referenced by a `@font-face`.
- T1 asserts `index.html` has no external `<link>`/preconnect.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (uncommitted)
- Host: Windows / pwsh, branch `feature/frontend-vue-migration`
- Browser(s): n/a (T2 deferred)

## Verdict
- Implementer: PASS (T1), DEFERRED (T2), 2026-09-11 07:13 UTC
- Verifier: <pending>
