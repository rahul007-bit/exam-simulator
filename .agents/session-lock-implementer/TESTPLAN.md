# TESTPLAN — session-lock

Per-task test plan.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `python tests/test_session_owner_lock.py` | 11 tests pass | PASS | |
| T2 | compile | `python -m py_compile web/server.py` | exit 0, no output | PASS | |
| T3 | unit | `_owner_decision(None,'c',False)` | `claim` | PASS | |
| T4 | unit | `_owner_decision('a','a',False)` | `allow` | PASS | |
| T5 | unit | `_owner_decision('a','b',False)` | `reject` | PASS | |
| T6 | unit | `_owner_decision('a',None,False)` / `(None,None,False)` | `allow`, no claim | PASS | |
| T7 | unit | `_owner_decision('a','b',True)` | `allow` (admin bypass) | PASS | |
| T8 | unit | `_owner_mismatch` first touch | claims owner and allow | PASS | |
| T9 | review | GET `/api/session` mismatch | locked payload | PASS (code review) | |
| T10 | review | HTTP candidate endpoints mismatch | 409 contract detail | PASS (code review) | |
| T11 | review | WS attach mismatch | close 1008 contract reason | PASS (code review) | |
| T12 | review | cookieless script | allowed, no claim | PASS (code review) | |

## Edge cases / additions
- `session_id` `"active"`/`"default"` sentinel resolved to the active session id
  on `/ws/session/{session_id}`.
- Owner cleared on `start` replacing an old session, submit, admin
  terminate/reset/end, and candidate reset/end.

## Environment
- Commit / build: 4789371 (working tree, not committed)
- Host: win32 / Python 3.12.4 (fastapi not installed; test avoids importing it)
- Branch: feature/frontend-vue-migration

## Verdict
- Implementer: PASS, 2026-09-11T08:35:35Z
- Verifier: pending
