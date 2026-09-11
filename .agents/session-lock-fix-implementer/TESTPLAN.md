# TESTPLAN — session-lock-fix

Per-task test plan.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | compile | `python -m py_compile web/server.py` | exit 0, no output | PASS | |
| T2 | unit | `python tests/test_session_owner_lock.py` | 11 tests pass | PASS | |
| T3 | review | `restore_session` calls `_enforce_owner` before `_claim_owner` | 409 for non-owner; admin/no-cookie allow | PASS (code review) | |
| T4 | e2e | `npx playwright test tests/e2e/session-locked.spec.ts` | locked card visible; start/workspace hidden; Retry -> start-exam | PASS | |
| T5 | lint | `bun run lint` (web/frontend) | exit 0 | PASS | |
| T6 | types | `bunx vue-tsc --noEmit` (web/frontend) | exit 0 | PASS | |
| T7 | unit | `bun run test` (web/frontend) | 22 files / 230 tests pass | PASS | |
| T8 | e2e | `npx playwright test` (web/frontend) | 21 tests pass | PASS | |

## Gap 1 detail
- `_enforce_owner(request, session_id)` raises HTTP 409 with detail
  `"This exam session is active in another window or device."` when
  `_owner_mismatch` is true.
- `_owner_mismatch` -> `_owner_decision`: `is_admin` => allow; `cid is None` =>
  allow (no claim); owner None => claim; owner == cid => allow; else reject.
- Placed immediately before the existing `_claim_owner(session_id, cid)`, so the
  old takeover (overwrite owner) can no longer happen.

## Gap 2 detail
- First `/api/session` fetch: locked payload
  `{active:false, session:null, locked:true, locked_preset:null, is_admin:false}`.
- `session-locked` visible; `start-exam` hidden; `candidate-workspace` hidden.
- Retry button (`session-locked-retry`) triggers `fetchSession` -> second
  `/api/session` response (`INACTIVE_SESSION`) -> `start-exam` visible and
  `session-locked` hidden; fetch counter >= 2.

## Environment
- Commit / build: working tree on `feature/frontend-vue-migration` (not committed)
- Host: win32 / Python 3.12.4 (fastapi not installed; unit test AST-extracts
  helpers) / Bun + Playwright 1.49
- Playwright webServer: fresh `npm run dev`, `VITE_BACKEND=http://127.0.0.1:9`
  (dead), so specs are deterministic/offline.

## Verdict
- Implementer: PASS, 2026-09-11T08:43:15Z
- Verifier: pending
