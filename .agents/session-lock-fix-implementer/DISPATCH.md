# DISPATCH — session-lock-fix

## 2026-09-11T08:43:15Z
You are assigned task **session-lock-fix** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/session-lock-fix-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Close two gaps found by an independent verifier:

1. **Takeover vector** — `POST /api/session/restore` (`web/server.py`, ~line
   1314) claimed the restored session's owner without first enforcing
   ownership, letting any caller who knows a `session_id` overwrite
   `session:{sid}:owner` and steal the lock.
2. **Missing E2E** — no Playwright coverage for the locked UI.

### Acceptance criteria
1. In `restore_session`, call `_enforce_owner(request, session_id)` **before**
   `_claim_owner(session_id, cid)`. Non-owner/non-admin → 409 with the contract
   detail; admin bypass and the `cid is None` allow path preserved.
2. `tests/e2e/session-locked.spec.ts`: mock `GET /api/session` locked
   (`{active:false, session:null, locked:true, locked_preset:null, is_admin:false}`),
   assert `session-locked` visible and `start-exam` / `candidate-workspace`
   hidden; click Retry (second `/api/session` response = normal inactive) and
   assert `start-exam` appears.

### Verification method
- `python -m py_compile web/server.py`
- `python tests/test_session_owner_lock.py`
- From `web/frontend/`: `bun run lint`, `bunx vue-tsc --noEmit`,
  `bun run test`, `npx playwright test` (expect 21 passing).

### Constraints
- One focused change per gap; no commit/amend/push; do not run
  `scripts/agents_board.py`.
- Update `EVIDENCE.md` with proof.
