# BRIEFING — FE-014

## Mission
Remove any glow/decorative-animation/emoji usage from the UI-system sources and add a
single inline-SVG `Icon` component that covers every glyph the UI currently needs, so
the M2 surface stays on the D-003 "calm, token-only, no AI-slop" visual language.

## 🔒 Identity
- Task: FE-014
- Role: implementer
- Working directory: .agents/FE-014-implementer-11
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-002, FE-005 (both verified)
- **Acceptance criteria:** (mirror the task entry)
  1. no box-shadow glow, no text-shadow, no decorative keyframes
  2. no emoji in UI copy
  3. icon set covers all current glyph needs
  4. existing tests still pass
- **Test cases:** (mirror `tasks.json` → `tests`; results in TESTPLAN.md)
  1. T1 (audit) grep `box-shadow|text-shadow|blur(` in `src/assets/styles` → no glow/shadow on UI chrome
  2. T2 (audit) grep emoji ranges in `src` → no emoji in UI copy
- **Verifier:** independent-agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Tokens/Tailwind only; no raw hex (`hex-audit.test.ts`).
- Strict file ownership (parallel batch): only Icon.vue, `components/ui/**`,
  Toaster.vue, ConfirmDialog.vue, DevUiView.vue, base.css,
  tests/unit/decor-audit.test.ts.
- Do not run the board CLI / build / Playwright during the batch.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: listed above

## Artifact index
- `.agents/FE-014-implementer-11/DISPATCH.md`
- `.agents/FE-014-implementer-11/progress.md`
- `.agents/FE-014-implementer-11/EVIDENCE.md`
- `.agents/FE-014-implementer-11/TESTPLAN.md`
