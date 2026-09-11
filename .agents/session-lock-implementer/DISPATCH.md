# DISPATCH — session-lock

## 2026-09-11T08:35:35Z
You are assigned task **session-lock** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/session-lock-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Soft per-session owner lock in `web/server.py` keyed on the `cka_client_id`
cookie, enforced on candidate HTTP endpoints and WebSockets, bypassed by admins
and cookieless internal tooling.

### Acceptance criteria
1. `session:{sid}:owner` = owning client id, TTL 86400.
2. Mismatched HTTP calls get 409; `/api/session` returns the locked payload.
3. Mismatched WS attach closes 1008 with the contract reason.
4. No cookie → never rejected, never claims.
5. Admins bypass; same-browser refresh still attaches.
6. Owner cleared when the session ends/changes.

### Verification method
- `python tests/test_session_owner_lock.py`
- `python -m py_compile web/server.py`
- Manual review of each changed endpoint/WS against the contract.

### Constraints
- One focused change; preserve parity (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof.
