# BRIEFING — FE-026

## Mission
Deliver the noVNC desktop island (`NoVncFrame.vue`) and the 36px segmented
Desktop/Terminal workspace control (`WorkspaceTabs.vue`), backed by URL +
`postMessage` helpers (`useVnc.ts`), preserving the legacy iframe URL/params and
`allow` contract exactly (D-007).

## 🔒 Identity
- Task: FE-026
- Role: implementer
- Agent: implementer-18
- Working directory: .agents/FE-026-implementer-18
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-003 (verified)
- **Deliverable:** `NoVncFrame.vue` + segmented Desktop/Terminal switch preserving
  iframe URL/params.
- **Acceptance criteria:**
  1. desktop iframe URL/params match current behavior
  2. tab switch preserves iframe state
  3. clipboard/allowed attrs preserved
- **Test cases:** (canonical in `tasks.json`; recorded in TESTPLAN.md)
  1. T1 manual — load desktop tab; noVNC connects; iframe src/params match legacy
  2. T2 manual — switch tabs and back; desktop session preserved
- **Verifier:** independent-agent

## Key constraints
- Strict parity (D-007): preserve the noVNC URL/params and `allow` attrs verbatim.
- Tokens/Tailwind only; no raw hex, glow or emoji.
- No new deps. `XTerm.vue` (FE-025) is imported read-only.
- Testing paused this batch: only `bunx vue-tsc --noEmit` may run.

## Pointers
- Legacy URL: `web/static/js/app.js:1655`; allow: `web/static/index.html:142`
- Legacy admin view-only URL: `web/static/js/admin.js:778`
- Legacy postMessage: `web/static/js/app.js:156-167`, `:260-266`
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope:
  - `web/frontend/src/components/workspace/NoVncFrame.vue`
  - `web/frontend/src/components/workspace/WorkspaceTabs.vue`
  - `web/frontend/src/composables/useVnc.ts`

## Artifact index
- `.agents/FE-026-implementer-18/DISPATCH.md`
- `.agents/FE-026-implementer-18/progress.md`
- `.agents/FE-026-implementer-18/EVIDENCE.md`
- `.agents/FE-026-implementer-18/TESTPLAN.md`
