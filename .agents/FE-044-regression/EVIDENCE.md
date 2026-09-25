# FE-044 — Full regression against the real backend — EVIDENCE

Date: 2026-09-25 09:15–09:20 IST
Repo: C:\Users\HP\Projects\4-sep-test\cka-labs @ feature/frontend-vue-migration, clean at bb81b2e (verified with `git status`/`git log -1`).

## 1. Backend suite (local, Windows host)

Command: `.venv/Scripts/python.exe -m unittest discover -s tests`
Result: **107 tests, 105 passed, 7 skipped (all "fastapi/httpx not available" or "host-only (Unix pty/termios)"), 1 error**

- EXPECTED (known Windows host-only, accepted per task brief):
  - ERROR test_recorder.TestSessionRecorder.test_record_shell_execution — `ModuleNotFoundError: No module named 'termios'` (Windows pty availability).
- UNEXPECTED (regression candidate — see section 5):
  - FAIL test_preset_authz.PresetAuthzSourceTest.test_handlers_call_require_admin (handler='generate_preset')

First 10 lines of unexpected traceback:
```
Traceback (most recent call last):
  File "tests\test_preset_authz.py", line 52, in test_handlers_call_require_admin
    self.assertTrue(
  File "tests\test_preset_authz.py", line 31-37, in _calls_require_admin (helper)
    ...
AssertionError: False is not true : generate_preset does not call require_admin
```

## 2. Frontend suite (web/frontend)

- `bun run lint` — PASS (eslint, exit 0)
- `bunx vue-tsc --noEmit` — PASS (exit 0, no type errors)
- `bun run test` (vitest) — PASS: **283 passed (283), 28 test files**, 0 failed.

## 3. Playwright E2E

- Port 5173: checked via netstat — already free (no PID to kill).
- `npx playwright test` — **21 passed (15.2s)**, 0 failed.
- Env note: Playwright started the vite dev server itself; visible `[vite] http proxy error: ECONNREFUSED 127.0.0.1:9` for /api/* — expected, no backend is configured for the dev server in E2E mode, and the tests pass regardless.

## 4. Live host (root@10.8.0.15 over VPN) — READ-ONLY probes only

- `systemctl is-active k8s-web` → **active**
- `journalctl -u k8s-web -n 50 --no-pager` → **no ERROR entries**. Content: normal INFO request logs; two clean stop/start cycles at 09:04:38 and 09:04:57; catalog pre-warm ("111 questions cached in Redis"); orphan sweep tearing down two stale session sandboxes (k3d clusters 'cka-1789538961', 'cka-1788775610') at 09:05:28–09:06:13. No tracebacks, no tracebacks-level errors.
- GET probes (curl status codes, unauthenticated):
  - `http://127.0.0.1:3000/` → 200 (SPA served)
  - `/api/assignments` → 401 (auth gate works)
  - `/api/presets` → 401 (auth gate works)
  - `/api/health` → 404 (route not present)
- Git on host: `/root/cka-labs` at `e32cb65 fix(platform): orphan sweep reclaims active_sessions ids with no session record`.
- No POST/PUT/DELETE probes, no service restarts.

## 5. Assessment of the failure

The suite contains an assertion contradiction. tests/test_preset_authz.py (line 47-55) asserts that all three preset handlers call `require_admin` in their source. However, since commit `FS-003b` / the vue-migration refactor (`a9b18cd` "refactor(web): split server monolith into web/api..."), the handler `generate_preset` correctly uses `require_user` (so any signed-in candidate can generate; verified in web/api/routes/presets.py lines 46-50 + FS-003b note "replace only the caller's own previous session"). The behavioral test `test_generate_preset_rejects_anonymous` correctly PASSES (anonymous → 401).

Conclusion: the source-level assertion for `generate_preset` in tests/test_preset_authz.py is stale with respect to the FE/FS-003b security model change; the handler behavior itself is correct. This is a test-corpus fix, not a code regression. F-outstanding: 1 beyond the 3 known host-only fails from the brief.

## 6. Board action

FE-044 status left as **todo** (not verified) because of the above 1 unexpected backend failure.

## Follow-up (2026-09-25, later same day)

- Stale AST assertion in `tests/test_preset_authz.py` fixed: `GATED_HANDLERS`
  is now a per-handler guard map (`get_presets`/`select_preset` -> require_admin,
  `generate_preset` -> require_user per FS-003b/FS-006). Test renamed to
  `test_handlers_call_expected_guard`; behavioral 401 tests unchanged and passing.
- Backend re-run: 107 tests, errors=1 (termios pty, known Windows host-only),
  skipped=7 — no other failures.
- Frontend suites (from subagent run): lint PASS, vue-tsc PASS, vitest 283/283,
  Playwright 21/21.
- Host at e32cb65: active, clean journal, read-only GET probes OK.

## Status: VERIFIED
