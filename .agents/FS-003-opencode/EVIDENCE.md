# EVIDENCE — FS-003 Session ownership model (+ var/session.json retired)

Agent: opencode. Date: 2026-09-11. Depends on FS-001 (verified).
User directive: do not maintain `var/session.json` — Redis is the session store.

## Deliverable
- `core/models.py` — `ExamSession.owner_username` + `assigned_by` (defaults
  None, in `to_dict()`).
- `core/redis_bus.py` — in-memory session-state fallback when Redis is
  unavailable (dev/CLI/tests); Redis remains authoritative when up (no double
  store). `create_invitation(..., assigned_by="")`; `list_session_history`
  returns ownership.
- `core/deployer.py` — **no file writes/reads**; `save_session` → Redis store;
  `load_active_session` → store only, with a one-time legacy-file migration
  (parse → persist → rename `<file>.migrated`); `clear_active_session` clears
  the store + unlinks any legacy file; `_cleanup_cluster_resources` reads the
  store. `session_file` arg kept for backward compat only.
- `core/recorder.py` — auto-attach reads the store instead of the file.
- `web/api/session_ownership.py` (new) — `record_session_owner` (writes
  `session:{sid}:owner_user`, `:assigned_by`, `user:{owner}:sessions`) and
  `get_user_sessions`; injectable bus for tests.
- `web/api/routes/session.py` — `get_timer` reads the store (identical response
  shape); `restore_session` drops the file fallback and preserves ownership.
- `web/api/routes/exam.py`, `routes/presets.py` — populate owner/assigned_by at
  session creation; invitations carry the assigning admin.
- `web/api/routes/admin.py` — invite records assigner; list/detail expose
  ownership. `web/api/services/session_view.py` — ownership in payloads.
- Acceptance: sessions owned by user ✔; assigned_by recorded ✔; migration test
  of legacy session data ✔.

## Tests / verification
- `tests/test_session_store.py` (new): legacy `.json` → `.migrated` migration,
  ownership round-trip, `clear_active_session`, ownership index with fake bus.
- `tests/test_recorder.py` deployer test updated to assert store cleared (it
  now **passes**, was previously erroring on this host).
- Full suite `python -m unittest discover -s tests` → 68 tests; only 2
  pre-existing host-only failures remain (termios, Firefox history). No
  regressions.
