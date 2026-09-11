# EVIDENCE — FS-006 Dynamic preset generator API

Agent: opencode. Date: 2026-09-11. Design: decisions.md D-010.

## Deliverable
- `web/api/services/preset_generator.py` — `generate_questions(count,
  difficulty?, domains?, selector?)`: pure logic, validates count (1..50),
  difficulty (easy/medium/hard/crazy, case-insensitive), domains (known Domain
  values); maps strings to core.models enums; delegates to
  `QuestionSelector.select_custom` (core/selector.py:54); empty selection →
  ValueError. Selector injectable for tests.
- `web/api/routes/presets.py` — POST `/api/presets/generate`
  (GeneratePresetRequest): 400 on ValueError; starts a session mirroring
  start_exam (deploy_sequential → token → save → register_token → Redis state →
  owner claim → touch activity → provision → deploy_step 0); responds with
  `build_session_payload(request)` — contains only the current task, never a
  question list (acceptance: "creates session without listing questions" ✔;
  "selects N questions by difficulty" ✔).
- Existing GET /api/presets + POST /api/presets/select unchanged.

## Tests
- `tests/test_preset_generator.py` — 12 cases (stub selector, no Redis/JSON
  catalog/fastapi needed): count validation, unknown difficulty/domain,
  case-insensitivity, enum kwargs passed to select_custom, count truncation,
  empty-pool rejection. All pass on Windows.
