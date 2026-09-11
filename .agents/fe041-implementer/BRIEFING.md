# BRIEFING — FE-041

## Mission
Self-host Inter + JetBrains Mono (and keep all libs bundled) so the Vue frontend
loads and renders correctly fully offline with no runtime CDN calls.

## 🔒 Identity
- Task: FE-041
- Role: implementer
- Working directory: .agents/fe041-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** none
- **Acceptance criteria:** (mirror the task entry)
  1. No runtime CDN calls; Inter + JetBrains Mono + all libs bundled.
  2. Network tab shows no external requests; assets served from same origin; offline load renders correctly.
- **Test cases:** (mirror `tasks.json` → `tests`)
  1. T1 (audit): scanned sources contain no external domains; `@font-face` for both families uses `/fonts/`; referenced woff2 exist.
  2. T2 (manual): load the app offline → styled + functional (DEFERRED here).
- **Verifier:** independent agent

## Key constraints
- Follow `decisions.md` — no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Do not self-certify; an independent verifier must sign off.
- No new package.json deps — vendor font files instead.
- Do NOT change `tokens.css` values; family names stay `Inter` / `JetBrains Mono`.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/public/fonts/**`, `web/frontend/src/assets/styles/fonts.css`,
  `web/frontend/src/assets/styles/base.css`, `web/frontend/tests/unit/offline-audit.test.ts`

## Artifact index
- `.agents/fe041-implementer/DISPATCH.md`
- `.agents/fe041-implementer/progress.md`
- `.agents/fe041-implementer/EVIDENCE.md`
