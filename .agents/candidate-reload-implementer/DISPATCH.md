# DISPATCH — candidate-reload

## 2026-09-10 15:51 UTC
You are assigned task **candidate-reload** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/candidate-reload-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Working header overflow **Reload** action on the candidate exam page. In
`web/frontend/src/views/CandidateView.vue`, add a typed template ref to
`<WorkspaceTabs>` and replace the `case 'reload':` TODO no-op: guard a missing
ref, then `terminal.reconnect()` when `activeTab === 'terminal'`, else
`vnc.reload()`. Optionally add `web/frontend/tests/unit/candidate-reload.test.ts`.

### Acceptance criteria
1. Terminal tab active → `terminal.reconnect()`.
2. Otherwise (desktop/noVNC) → `vnc.reload()`.
3. Missing instance/ref → safe no-op, never throws.
4. All existing switch cases intact; `new-tab` remains out of scope/no-op.
5. `bunx vue-tsc --noEmit` and `bun run lint` pass.

### Verification method
- `bunx vue-tsc --noEmit`
- `bun run lint`
- `bunx vitest run tests/unit/candidate-reload.test.ts`
(the orchestrator runs the full suite separately)

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Edit only `CandidateView.vue` + own test/workspace; do not touch
  `WorkspaceTabs.vue` or Badge/TaskPane/task.ts.
- No commit/amend/push. Do not run `bun run build` or Playwright.
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.
