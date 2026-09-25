# Progress — badge-copy

## Current status
Last visited: 2026-09-10 (UTC)
Status: in-review
Owner: implementer-badge-copy
Verifier: independent agent

## Checklist
- [x] Read PLAN.md + decisions.md
- [x] Implement deliverable
- [x] Meet all acceptance criteria
- [x] Capture evidence (commands/output) in EVIDENCE.md
- [ ] Independent verification
- [ ] Update tasks.json status

## Iteration status
Current iteration: 1 / 32

## Retrospective notes
- Badge copy support kept strictly opt-in so admin/non-copyable usages are
  byte-for-byte unchanged.
- QuestionDrawer per-task card converted from `<button>` to
  `<div role="button" tabindex="0">` to avoid nested interactive controls.
- PresetModal "Selected" badges excluded (selection state + nested in buttons).
- Follow-up `implementer-badge-fix`: added `@keydown.stop` to the copyable
  Badge button so Enter/Space no longer bubble to the drawer card's
  `@keydown.enter`/`@keydown.space` jump handler (`.stop` preserves the native
  activation, so keyboard copy still works).
- Follow-up: `context:`/`ns:` chips now copy only the raw value via an optional
  `TaskBadge.copy` field and `:copy-text="badge.copy ?? badge.label"` in
  `TaskPane.vue`.
