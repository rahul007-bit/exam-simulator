# DISPATCH — FE-020

## 2026-09-10 11:00 UTC
You are assigned task **FE-020** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-020-implementer-14`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
AppShell + 52px candidate header (exam name, progress, timer, Flag, Submit,
`⋯` overflow) inside `src/components/layout/**`, consumed by `CandidateView.vue`.

### Acceptance criteria
1. Header shows only primary controls; everything secondary is in one overflow menu.
2. Session-id copy and admin End/Reset live in the overflow.
3. Responsive at 1366x768 and 1920x1080 with no overflow/clipping.

### Verification method
- `bunx tsc --noEmit` (batch rule; must exit 0).
- After the batch: `bun run build` + Playwright at 1366x768/1920x1080, and an
  axe pass on the candidate route (host-only, DEFERRED locally).
- Visual/overflow audit of `[data-testid="candidate-header"]`.

### Constraints
- One focused change; strict file ownership (layout/** + CandidateView.vue only).
- Preserve parity behavior (D-007). FE-023 `useTimer`, FE-024 components and
  FE-012 primitives are read-only imports.
- Leave `TODO(integration)` for FE-021/025/026/027/028/029 rather than editing
  their files.
- Testing is paused for this batch: run only `bunx tsc --noEmit`.
