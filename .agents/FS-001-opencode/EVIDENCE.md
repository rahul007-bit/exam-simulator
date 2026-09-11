# EVIDENCE — FS-001 Auth backend (users, roles, hashing, login/logout)

Agent: opencode. Date: 2026-09-11. Design decisions: decisions.md D-010
(Redis users, stdlib pbkdf2, Redis session cookie — user-confirmed).

## Deliverable
- `web/api/users.py` — Redis user store (`user:{username}` hash + `users` set),
  pbkdf2_sha256 hashing (390k iters, 16-byte salt, `hmac.compare_digest`),
  create/get/list/delete user, `ensure_bootstrap_admin()` (env
  `AUTH_ADMIN_USER`/`AUTH_ADMIN_PASSWORD` fallback `ADMIN_PASSWORD`).
- `web/api/auth_sessions.py` — opaque session tokens at `auth:session:{token}`
  (TTL 604800), httponly cookie `cka_auth_token` + Bearer support, destroy.
- `web/api/security.py` — `is_admin_authenticated` extended: a valid auth
  session with role "admin" passes (step 4, deferred import); `require_admin`
  helper (401).
- `web/api/routes/auth.py` — POST `/api/auth/login`, POST `/api/auth/logout`,
  GET `/api/auth/me`, POST `/api/admin/users`, GET `/api/admin/users`
  (admin-only via `require_admin`).
- `web/api/__init__.py` — auth router registered; `ensure_bootstrap_admin()`
  called in the startup hook (error-tolerant).
- Acceptance: roles admin/user ✔; secure hashing (pbkdf2, salted, constant-time)
  ✔; session cookie ✔.

## Tests
- `tests/test_auth_users.py` — 29 cases: 23 unit (fake Redis bus via
  mock.patch) + 6 endpoint tests (skip on Windows without fastapi).
- Windows run: `python -m unittest tests.test_auth_users` → 23 pass, 6 skip.
- Host-only endpoint tests must be re-run on the host during FE-044.
