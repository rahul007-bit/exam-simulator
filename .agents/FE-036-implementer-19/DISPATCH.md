# DISPATCH — FE-036

## 2026-09-10T11:12:29Z
You are assigned task **FE-036** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-036-implementer-19`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Admin reset/terminate/end UX: reduce excessive dialog margin and make
long-running actions non-blocking (GCP-style) so one in-flight action never locks
the rest of the admin sessions page.

### Acceptance criteria
1. admin action/confirm dialogs use tighter, consistent spacing (no excessive margin/padding)
2. starting an action shows a per-row/inline busy state but does NOT block opening or acting on other sessions
3. the sessions table stays populated during a mutation (no full-table loading blank); only the affected row's actions are disabled
4. results are still reported via toast and actions still go through the promise confirm dialog (no native dialogs)

### Verification method
- `bunx vue-tsc --noEmit` (mandatory; testing paused)
- unit: `useAdminSessions` exposes per-row pending state (`isRowPending`/`isPending`/`pendingActionFor`)
- e2e (host-only, DEFERRED locally): while one row is resetting, another row can be opened and actioned

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Testing paused: do not run test/build/Playwright/board CLI.
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.
