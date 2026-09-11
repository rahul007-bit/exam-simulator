# EVIDENCE — FS-007 Custom exam builder UI

Agent: opencode. Date: 2026-09-11. Depends on FS-006 (verified). Design: D-011.

## Deliverable
- `web/frontend/src/api/presets.ts` — added `generatePreset(body)` +
  `GeneratePresetRequest`/`GeneratePresetResponse` (+ difficulty/domain unions),
  calling `POST /api/presets/generate`. Existing exports untouched.
- `web/frontend/src/components/admin/PresetBuilder.vue` (new) — Card "Custom
  exam": count (1–50), optional difficulty, optional domain checkbox chips;
  "Generate & start" calls the FS-006 endpoint and renders only a summary line
  ("Started session with N tasks") — **never a question list**; mounted in
  `AdminView.vue` by the orchestrator.
- `web/frontend/tests/unit/preset-builder.test.ts` (new): 7 tests (count limits,
  difficulty/domains passthrough, success summary with no question render,
  error toast).
- Acceptance: generates and starts exam ✔; no individual questions shown ✔.

## Tests / verification (orchestrator consolidated pass)
- Frontend: lint + `vue-tsc` clean; `bun run test` → 242 tests (24 files);
  build; `npx playwright test` → 21 passed.
- Backend suite unaffected (75 tests, same 2 host-only failures).
