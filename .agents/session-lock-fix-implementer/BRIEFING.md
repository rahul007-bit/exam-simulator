# BRIEFING — session-lock-fix

## Mission
Close two gaps found by an independent verifier in the per-session owner lock:
(1) `POST /api/session/restore` was a takeover vector (claimed the owner without
first enforcing ownership) and (2) the locked UI had no E2E coverage.

## 🔒 Identity
- Task: session-lock-fix
- Role: implementer
- Working directory: .agents/session-lock-fix-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** session-lock (backend) + session-lock-fe (frontend UI)
- **Acceptance criteria:**
  1. `restore_session` calls `_enforce_owner` before `_claim_owner`, so a
     non-owner/non-admin gets HTTP 409
     `"This exam session is active in another window or device."`; admin bypass
     and the `cid is None` allow path are preserved.
  2. New Playwright spec `tests/e2e/session-locked.spec.ts` proves the locked
     card is shown (and `start-exam` / `candidate-workspace` are not) and that
     Retry re-fetches `/api/session` into the start screen.
- **Test cases:** `python -m py_compile web/server.py`,
  `python tests/test_session_owner_lock.py`, frontend lint/typecheck/unit and
  `npx playwright test`.
- **Verifier:** independent agent

## Key constraints
- Surgical change to `restore_session` only.
- Do not touch `web/frontend/src/**` (already implemented) or other tests.
- Do not run `scripts/agents_board.py`; no commit/amend/push.

## Pointers
- Files in scope: `web/server.py` (restore_session only),
  `web/frontend/tests/e2e/session-locked.spec.ts`,
  `web/frontend/tests/e2e/helpers.ts` (tiny helper only, if needed)

## Artifact index
- `.agents/session-lock-fix-implementer/DISPATCH.md`
- `.agents/session-lock-fix-implementer/progress.md`
- `.agents/session-lock-fix-implementer/EVIDENCE.md`
- `.agents/session-lock-fix-implementer/TESTPLAN.md`
