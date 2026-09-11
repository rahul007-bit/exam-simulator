# BRIEFING — session-lock

## Mission
Add a soft per-session owner lock to the FastAPI backend so only the owning
client (per-browser `cka_client_id` cookie) — plus admins and cookieless
internal tooling — can attach to the single global active exam session.

## 🔒 Identity
- Task: session-lock
- Role: implementer
- Working directory: .agents/session-lock-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** none
- **Acceptance criteria:**
  1. Owner key `session:{sid}:owner` written on claim, TTL 86400, via
     `redis_bus.get_sync_client()`.
  2. A different client gets HTTP 409 `"This exam session is active in another window or device."`
     and `/api/session` returns `{"active": False, "session": None, "locked": True, "locked_preset": None, "is_admin": ...}`.
  3. WS attach from a different client closes `1008` with reason
     `"Session active in another window or device"`.
  4. `cid is None` (scripts/curl/workers) is never rejected and never claims.
  5. Admins always bypass; same cookie refresh keeps working.
  6. Owner cleared on submit/terminate/reset/end/session change.
- **Test cases:** `python tests/test_session_owner_lock.py`, `python -m py_compile web/server.py`
- **Verifier:** independent agent

## Key constraints
- Only `redis_bus.get_sync_client()`; no new dependencies.
- Do not touch `web/frontend/**`, `core/**`, `docker/**`, board files.
- Do not break admin endpoints or `scripts/verify_platform_api.py`.

## Pointers
- Files in scope: `web/server.py`, `tests/test_session_owner_lock.py`

## Artifact index
- `.agents/session-lock-implementer/DISPATCH.md`
- `.agents/session-lock-implementer/progress.md`
- `.agents/session-lock-implementer/EVIDENCE.md`
- `.agents/session-lock-implementer/TESTPLAN.md`
