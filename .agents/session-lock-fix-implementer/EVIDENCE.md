# EVIDENCE — session-lock-fix

## Implementer — implementer-session-lock-fix (2026-09-11T08:43:15Z)

### Deliverable
Closed the two verifier gaps in the per-session owner lock.

### Gap 1 — restore takeover (`web/server.py`, `restore_session`)
Before:
```python
    _claim_owner(session_id, cid)
```
After:
```python
    # Enforce ownership before (re)claiming: a non-owner/non-admin must not be
    # able to overwrite the owner lock by restoring someone else's session.
    _enforce_owner(request, session_id)
    _claim_owner(session_id, cid)
```
`_enforce_owner` raises HTTP 409 `"This exam session is active in another window
or device."` for a non-owner/non-admin. Admin bypass and the `cid is None` allow
path are inherited unchanged from `_owner_decision`. The change is surgical: it
only adds the enforcement call immediately before the existing claim.

### Gap 2 — E2E coverage for the locked UI
New `web/frontend/tests/e2e/session-locked.spec.ts` (one test, uses
`stubBrowserApis` + `mockApi` from `helpers.ts`). The `/api/session` stub is a
stateful factory: first call returns
`{active:false, session:null, locked:true, locked_preset:null, is_admin:false}`,
later calls return the normal `INACTIVE_SESSION`. Asserts:
- `session-locked` visible while `start-exam` and `candidate-workspace` are
  hidden (locked card wins).
- After clicking `session-locked-retry`, `session-locked` is hidden and
  `start-exam` is visible, and the stub recorded >= 2 `/api/session` fetches
  (proving Retry re-fetches).

No `helpers.ts` change was needed (factory inline).

### Files touched
- `web/server.py` (`restore_session` only)
- `web/frontend/tests/e2e/session-locked.spec.ts` (new)
- `.agents/session-lock-fix-implementer/**` (this workspace)

### Commands run + output
```
PS> python -m py_compile web/server.py
py_compile exit=0

PS> python tests/test_session_owner_lock.py
............
Ran 11 tests in 0.359s
OK
exit=0

PS> bun run lint            # web/frontend
$ eslint .
lint exit=0

PS> bunx vue-tsc --noEmit   # web/frontend
vue-tsc exit=0

PS> bun run test            # web/frontend
Test Files  22 passed (22)
     Tests  230 passed (230)
unit exit=0

PS> npx playwright test     # web/frontend
Running 21 tests using 8 workers
  21 passed (7.4s)
e2e exit=0
```

### Notes / deviations
- The Vite dev server logs `http proxy error ... ECONNREFUSED 127.0.0.1:9` for
  `/api/session`, `/api/timer`, `/api/presets`; that is the intentional dead
  backend (`VITE_BACKEND=http://127.0.0.1:9`) and all specs mock `/api/**`
  themselves, so it is harmless.
- `bun run build` deliberately not run, per instructions.
- No commit/amend/push; `scripts/agents_board.py` not run.
- No deviation from the requested change set.

## Verifier — <different agent> (<UTC>)
- Pending.
