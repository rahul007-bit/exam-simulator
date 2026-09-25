# EVIDENCE — FS-008 Hide preset catalog from non-admin users

Agent: opencode. Date: 2026-09-11. Depends FS-002 (verified). Design: D-010.

## Deliverable
- Backend `web/api/routes/presets.py` — `require_admin(request)` added to
  `GET /api/presets`, `POST /api/presets/select`, and `POST /api/presets/generate`;
  non-admins get 401. Admin response bodies unchanged.
- Frontend `CandidateView.vue` (orchestrator-owned) — candidates no longer fetch
  the catalog on mount and the "Choose preset" button + `PresetModal` render only
  for admins (`auth.isAdmin`); `onStart` sends a preset only for admins.
- `tests/test_preset_authz.py` (new) — 401 behavior + source assertions.
- Acceptance: non-admin cannot enumerate presets ✔ (API 401 + UI hidden);
  API authorization enforced ✔.

## Tests / verification (orchestrator consolidated pass)
- Backend: 81 tests; only the 2 pre-existing host-only failures.
- Frontend: lint + tsc clean; 250 vitest; build; 21 Playwright (updated the
  FE-042 candidate specs: preset picker is now admin-only, so the candidate
  journey/a11y specs assert its absence).

## Deviation from D-010
- D-010 mentioned locking `GET /api/questions` too. It is **kept candidate-
  accessible**: it returns only the ACTIVE session's own question list (not a
  catalog), which the candidate UI needs. Only `/api/presets` is an enumerable
  catalog and is now admin-only.
