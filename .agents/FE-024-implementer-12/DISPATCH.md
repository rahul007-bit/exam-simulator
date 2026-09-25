# DISPATCH - FE-024

## 2026-09-10 10:48 UTC
You are assigned task **FE-024** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-024-implementer-12`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
question navigator, preset selector (admin), full curriculum card, final scorecard

### Acceptance criteria
1. navigator reflects flagged/current/score states
2. scorecard matches `/api/action/submit` payload (`scorecard[]` with
   `task_num, id, title, domain, context, score, max_score, passed, message`)
3. no emoji in preset cards

### Verification method
- `bun run test` (unit), `bunx tsc --noEmit`, `bunx vue-tsc --noEmit`, `bun run lint`
- Host (deferred): Playwright T1/T2 against the integrated `/exam` route.

### Constraints
- One focused change; only new files under `src/components/candidate/` and
  `tests/unit/question-*.test.ts` (see PROTOCOL §9).
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; the orchestrator owns `tasks.json` during the batch.
