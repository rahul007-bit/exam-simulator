# DISPATCH — FE-021

## 2026-09-10T11:12Z
You are assigned task **FE-021** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-021-implementer-17`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Persisted draggable split-pane workspace: default `[24,76]`, min `[300,520]`,
double-click reset, collapse-left toggle. Dependency-free implementation in
`composables/useSplitPane.ts` + `components/layout/WorkspaceSplit.vue`, wired into
`views/CandidateView.vue`. A marked `TODO(workspace-tabs)` slot is left for FE-026.

### Acceptance criteria
1. Right pane gets >= 76% by default.
2. Split ratio persists across reloads.
3. Collapse toggle maximizes the workspace.

### Verification method
- `bunx vue-tsc --noEmit` (batch rule: only this command; tests paused).
- Manual (host/deferred): load workspace, drag + reload, toggle collapse.
- Inspect `localStorage` key `cka:workspace:split`.

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; do not run the board CLI (batch).

### Batch rules (PROTOCOL §9)
- Testing paused: run only `bunx vue-tsc --noEmit`.
- Strict file ownership: `components/layout/**`, `views/CandidateView.vue`,
  `composables/useSplitPane.ts`. Do not touch App.vue/main.ts/router/package.json/
  configs/ui/**/workspace/**/candidate/**/admin/**/stores/**.
- Do not run `scripts/agents_board.py`.
