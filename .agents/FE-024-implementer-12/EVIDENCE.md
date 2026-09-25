# EVIDENCE - FE-024

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer - implementer-12 (2026-09-10 10:48 UTC)

- Deliverable: question navigator/drawer, admin preset selector modal with the
  full-curriculum card, and the final exam scorecard.
- Files created (all new; nothing shared touched):
  - `web/frontend/src/components/candidate/question.ts`
  - `web/frontend/src/components/candidate/scorecard.ts`
  - `web/frontend/src/components/candidate/QuestionDrawer.vue`
  - `web/frontend/src/components/candidate/PresetModal.vue`
  - `web/frontend/src/components/candidate/ExamScorecard.vue`
  - `web/frontend/tests/unit/question-nav.test.ts`
  - `web/frontend/tests/unit/question-scorecard.test.ts`

### Commands run + output

Targeted tests:
```
$ bun run test question
 ✓ tests/unit/question-scorecard.test.ts (6 tests) 66ms
 ✓ tests/unit/question-nav.test.ts (9 tests) 94ms
 Test Files  2 passed (2)
      Tests  15 passed (15)
```

Full unit suite (no regressions):
```
$ bun run test
 Test Files  16 passed (16)
      Tests  176 passed (176)
```
Includes the concurrent FE-014 `decor-audit.test.ts` and existing
`hex-audit.test.ts`, which both pass against the new candidate files.

Typecheck:
```
$ bunx tsc --noEmit        # (no output, exit 0)
$ bunx vue-tsc --noEmit    # EXIT:0
```

Lint:
```
$ bun run lint
$ eslint .
LINT_EXIT:0
```
Clean (0 errors, 0 warnings). An earlier run surfaced one warning in
`src/components/Icon.vue` (FE-014, implementer-11); it was fixed concurrently and
the final run is clean. No FE-024 file produced a lint finding.

Screenshots: n/a (component-level work; browser leg deferred per PROTOCOL §6).

### Test cases executed (see TESTPLAN.md)
- T1: PASS by equivalent (`question-nav.test.ts`; Playwright browser leg DEFERRED — host-only)
- T2: PASS by equivalent (`question-scorecard.test.ts`; Playwright browser leg DEFERRED — host-only)

### Self-check against acceptance criteria
1. **navigator reflects flagged/current/score states** — PASS. `navState()`
   implements the legacy precedence (`current > flagged > scored > pending`,
   `web/static/js/app.js:1456`); the drawer renders a token Badge per item and
   tests assert `data-state`, `aria-current`, labels and summary counts.
2. **scorecard matches `/api/action/submit` payload** — PASS. `scorecardRows()`
   maps exactly `task_num, id, title, domain, context, score, max_score, passed,
   message` (plus a display `scoreText`); tests assert every field and the
   rendered row cells, plus summary from `total_earned/total_possible/percentage/
   passed/threshold`.
3. **no emoji in preset cards** — PASS. `PresetModal.vue` uses text labels only
   ("Time limit", "Tasks", "Pass"); `decor-audit.test.ts` and `ui-primitives`
   emoji regex pass, and `hex-audit.test.ts` confirms no raw hex in
   `src/components/**`.

Regression checks (parity/WS/clipboard/timer): no behavior touched — FE-024 adds
presentational components and pure mappers only; no store, router, WS, timer or
clipboard code changed. Timer/markdown/stores suites all pass unchanged.

### Shared-file needs
None. Integration (wiring the drawer/scorecard/preset modal into
`CandidateView.vue`/`AdminView.vue` and fetching `/api/questions`) is the
orchestrator's step; `fetchQuestions()` is exported from `question.ts` for that.

## Verifier - <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> - PASS/FAIL - <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` - <reasons if rejected>
