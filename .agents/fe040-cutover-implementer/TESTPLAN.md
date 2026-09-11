# TESTPLAN — FE-040 (part 2: cutover)

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results.

Test cases are defined canonically in `tasks.json` (task `FE-040` → `tests`).

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | audit | `git grep -n -E 'web/static\|static/js\|static/css\|app\.js\|admin\.js\|admin\.html\|style\.css' -- . ':(exclude).agents' ':(exclude).worktrees'` | zero hits | PASS (exit 1, no output) | |
| T2a | unit | `python tests/test_frontend_cutover.py -v` | 3 pass, 1 skip | PASS (OK, skipped=1) | |
| T2b | host/browser | Serve a real build on a Unix host; GET `/`, `/admin`, `/login` | 200 + SPA mount; unknown `/api/*` → 404 | DEFERRED (Windows host) | |
| T3 | compile | `python -m py_compile web/server.py` | exit 0 | PASS | |

## Edge cases / additions
- Catch-all must be registered even when `web/dist` is absent (503, not 404).
- Path traversal (`..`) must not escape `web/dist`.
- `api`/`ws`/`novnc` first segment must never resolve to index.html.

## Environment
- Commit / build: dirty working tree on `feature/frontend-vue-migration`
- Host: Windows dev box (win32) — pty/termios + fastapi host-only leg skipped
- Browser(s): n/a (T2b deferred)

## Verdict
- Implementer: PASS, 2026-09-10T18:09:58Z
- Verifier: pending
