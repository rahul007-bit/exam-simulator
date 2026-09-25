# EVIDENCE — FS-003b Concurrent per-user sessions

Agent: opencode. Date: 2026-09-11. Depends FS-003 + FS-004 (verified).
Design: decisions.md D-012.

## Deliverable
- `core/redis_bus.py` — the `active_sessions` set is the registry;
  `set_session_state` registers + keeps the legacy `session:active:id` pointer
  (tools only); `is_session_active` is now **membership-only**; new
  `list_active_session_ids()`, `set/get/clear_user_active_session()`;
  `clear_session_state`/`archive_session` deregister + clear the user pointer.
  In-memory fallback mirrored for all of it.
- `web/api/session_resolver.py` (new) — contextual resolution: candidate token →
  the authenticated user's active session → (admins only) legacy pointer.
- `core/deployer.py` — `load_session(sid)`; `_session_from_state` helper;
  `clear_active_session(sid)` optional; `load_active_session` kept for CLI/tools.
- `routes/start_exam` + `presets/generate` — replace only the **caller's own**
  previous session; set the per-user active index; no global teardown.
- `background.py` — timer/expiry/idle workers iterate `list_active_session_ids()`
  and clear per-session (no global `clear_session`).
- `ws_terminal` / `ws_desktop` / `ws_events` — candidate access validates the
  explicit session id is active + owned (no `session:active:id` fallback).
- `admin_list_sessions`, `GET /api/sessions` — list all live sessions.
- `security.require_user` + `routes/presets.generate` relaxed from admin-only to
  any signed-in user (listing `/api/presets` stays admin-only).

## Tests / verification
- `tests/test_multi_session.py` (new, 5) — registry, per-user index, legacy
  pointer, membership; passes offline (in-memory path).
- Full backend suite: 86 tests; only the 3 known host-only failures
  (termios, k3d binary, Firefox history) — no regressions.
- Deployed to the host; `k8s-web.service` active, startup clean; GET probes 200.
- **Exercised live: two simultaneous provisioned sessions** — manually tested
  by Rahul on the host (2026-09-25), both sessions ran concurrently.

## Status: VERIFIED — live two-session concurrency manually tested by Rahul on the host (2026-09-25): two users ran exams concurrently, terminal/VNC resolved per session. Board flipped to verified 2026-09-25.
