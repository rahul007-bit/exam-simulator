# TESTPLAN - candidate-nav-parity

Test cases for the candidate navigation parity gaps.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run test` -> `tests/unit/task-pane.test.ts` | Footer renders progress text; emits `prev`/`next`/`reset`; Previous disabled first, Next disabled last, all disabled busy; no footer without task | PASS (5) | |
| T2 | unit | `bun run test` -> `tests/unit/question-nav.test.ts` | Uncontrolled drawer re-loads on every open (loader called twice across two opens) | PASS (1) | |
| T3 | e2e | `npx playwright test tests/e2e/candidate-journey.spec.ts` | Task footer Next -> Task 2 (next disabled / prev enabled); Prev -> Task 1; drawer jump + reopen marks Task Two current; submit scorecard | PASS | |
| T4 | lint | `bun run lint` | 0 errors | PASS | |
| T5 | typecheck | `bunx vue-tsc --noEmit` | 0 errors | PASS | |
| T6 | regression | `bun run test` | 224 passed (baseline 218 + 6 new) | PASS | |
| T7 | regression | `npx playwright test` | 20 passed | PASS (isolated fresh dev server; see EVIDENCE for env note) | |

## Edge cases / additions
- No task -> footer omitted entirely.
- `busy` disables Previous/Reset/Next even mid-list.
- Controlled drawer (`questions` prop) untouched by the refetch change.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (uncommitted)
- Host: Windows / pwsh, chromium via Playwright 1.49
- Browser(s): chromium (Desktop Chrome)

## Verdict
- Implementer: PASS, 2026-09-11 08:17 UTC
- Verifier: pending
