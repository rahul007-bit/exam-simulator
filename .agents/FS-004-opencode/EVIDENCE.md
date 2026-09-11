# EVIDENCE — FS-004 Admin assigns exam to user

Agent: opencode. Date: 2026-09-11. Depends on FS-003 (verified). Design: D-011
(assignments are user-bound invitations).

## Deliverable
- `core/redis_bus.py` — `create_invitation(token, preset, assigned_by="",
  assigned_to="")`; new `list_assignments()`, `get_user_assignments(username)`,
  `delete_assignment(token)`.
- `web/api/routes/assignments.py` (new) — POST/GET `/api/admin/assignments`
  (admin), DELETE `/api/admin/assignments/{id}` (admin), GET `/api/assignments`
  (current user via auth session). Registered in `web/api/__init__.py`.
- `web/frontend/src/api/assignments.ts` (new) — typed client.
- `web/frontend/src/components/admin/AdminAssignmentPanel.vue` (new) — assign
  form (user + preset) + assignments table with delete/confirm; mounted in
  `AdminView.vue` by the orchestrator.
- Acceptance: admin assigns preset to user ✔; assignment visible to the user
  (`GET /api/assignments` from their auth session) ✔.

## Tests / verification (orchestrator consolidated pass)
- `tests/test_assignments.py` (new): 6 pass; `tests/test_route_inventory.py`
  now also covers the new routes.
- Full backend suite: 75 tests; only the 2 pre-existing host-only failures.
- Frontend: lint + `vue-tsc` clean; 242 vitest; build; 21 Playwright.
- Host-only: API role flows against the real backend belong to FE-044.
