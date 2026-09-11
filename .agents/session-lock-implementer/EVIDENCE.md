# EVIDENCE — session-lock

## Implementer — implementer-session-lock (2026-09-11T08:35:35Z)
- Deliverable: Soft per-session owner lock keyed on the `cka_client_id` cookie.
  Owned client ids are stored at `session:{sid}:owner` (TTL 86400) through
  `redis_bus.get_sync_client()`. Candidate HTTP endpoints return the contract
  409; `/api/session` returns the locked payload; candidate WebSockets close
  1008. Admins always bypass; cookieless callers (scripts/curl/workers) are
  never rejected and never claim. Owner is cleared when a session ends/changes.
- Files touched:
  - `web/server.py`
  - `tests/test_session_owner_lock.py`
  - `.agents/session-lock-implementer/**` (this workspace)

### Helper / decision functions (web/server.py, after `is_admin_authenticated`)
- `_owner_decision(owner, cid, is_admin) -> "allow" | "claim" | "reject"` (pure)
- `_client_id(request)`, `_client_id_ws(websocket)`
- `_owner_key(sid)`, `_get_owner(sid)`, `_claim_owner(sid, cid)`, `_clear_owner(sid)`
- `_owner_mismatch(sid, cid, is_admin)` — claims on first touch, returns bool
- `_enforce_owner(request, sid)` — raises HTTP 409 with the contract detail

### Endpoints / WS changed
- `/api/session`: lock check → `{"active": False, "session": None, "locked": True, "locked_preset": None, "is_admin": ...}`
- `/api/start`: `_claim_owner` after token mapping; `_clear_owner` for the replaced session
- `/api/session/restore`: `_claim_owner` for the restored session
- Candidate enforcement (409): `/api/questions`, `/api/timer`, `/api/clipboard` GET+POST,
  `/api/action/next`, `/prev`, `/jump`, `/flag`, `/retry`, `/submit`, `/api/reset`, `/api/end`
- Owner cleared: submit success, admin `terminate`, admin `reset`, admin `end`,
  candidate `reset`/`end`, and session replacement on `start`
- WebSockets: `/ws/session/{session_id}` (active session only, handles
  `active`/`default` sentinel), `/ws/terminal` (+ `{session_id}`) candidate gate,
  `_proxy_vnc` candidate gate — all close `1008` with the contract reason
- `admin_end_session` now calls `action_submit(request)` so the admin context
  (and bypass) is preserved

### Commands run + output
```
PS> python -m py_compile web/server.py
py_compile OK

PS> python tests/test_session_owner_lock.py -v
test_admin_always_allows ... ok
test_different_owner_rejects ... ok
test_matching_owner_allows ... ok
test_missing_client_id_allows_without_claim ... ok
test_no_owner_with_client_id_claims ... ok
test_admin_bypasses_and_does_not_take_over ... ok
test_claim_on_first_touch_and_allow ... ok
test_empty_sid_is_allowed ... ok
test_no_client_id_allows_and_does_not_claim ... ok
test_other_owner_rejects_without_takeover ... ok
test_same_owner_allows ... ok
----------------------------------------------------------------------
Ran 11 tests in 0.351s

OK
```

### How internal tooling stays unblocked
`_owner_decision` returns `allow` whenever `cid is None`, and `_claim_owner`
no-ops on a `None` cid. `scripts/verify_platform_api.py`, curl, and the
`web/server.py` background workers (which call `load_active_session()` directly,
not via HTTP) therefore keep today's behaviour. Admins bypass via
`is_admin_authenticated` for HTTP and WebSockets.

### Self-check against acceptance criteria
1. Owner key + TTL via sync client — PASS
2. 409 contract shape / `/api/session` locked payload — PASS (code review)
3. WS close 1008 + contract reason — PASS (code review)
4. No cookie → allowed, no claim — PASS (unit + code review)
5. Admin bypass, same cookie refresh — PASS (unit: owner==cid allow)
6. Owner cleared on end/change — PASS (code review of all call sites)

### Deviations
- `tests/test_session_owner_lock.py` AST-extracts the shipped helper functions
  from `web/server.py` instead of importing `web.server`, because `fastapi` is
  not installed on the Windows host. This exercises the real shipped code.
- No commit/amend/push performed, per instructions.

## Verifier — <different agent> (<UTC>)
- Pending.
