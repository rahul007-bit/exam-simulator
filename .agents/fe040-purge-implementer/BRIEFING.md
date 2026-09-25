# BRIEFING — FE-040 (legacy removal / static cutover, part 1)

## Mission
Strict purge: remove every reference to the legacy vanilla-JS frontend from
`web/frontend/**` (code comments and tests included) so a repo-wide audit finds
no legacy tokens, ahead of the legacy file deletion handled by the next agent.

## 🔒 Identity
- Task: FE-040 (part 1 — frontend purge)
- Role: implementer
- Working directory: .agents/fe040-purge-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-039 (frontend migration tasks)
- **Acceptance criteria:**
  1. Zero matches for `web/static|static/js|static/css|app\.js|admin\.js|admin\.html|style\.css` under `web/frontend`.
  2. No bare legacy `file:line` citations remain.
  3. No runtime/behaviour change; lint + typecheck + 209 tests pass.
- **Test cases:** see TESTPLAN.md (T1–T3).
- **Verifier:** independent agent.

## Key constraints
- Follow `decisions.md` — D-007 strict parity preserved in reworded comments.
- Do NOT delete `web/static` or edit `web/server.py` (next agent).
- Do NOT commit/amend/push; do NOT run `bun run build`/Playwright.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/**` (comments/tests/docs only)

## Artifact index
- `.agents/fe040-purge-implementer/DISPATCH.md`
- `.agents/fe040-purge-implementer/progress.md`
- `.agents/fe040-purge-implementer/EVIDENCE.md`
