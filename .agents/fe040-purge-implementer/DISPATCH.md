# DISPATCH — FE-040 (purge part 1)

## 2026-09-10T18:07:23Z
You are assigned task **FE-040** (part 1) on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/fe040-purge-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Strict purge of all legacy vanilla-JS references from `web/frontend/**`, so that
`git grep -nE 'web/static|static/js|static/css|app\.js|admin\.js|admin\.html|style\.css' -- web/frontend`
returns zero hits. Comments rewritten to keep D-007 parity meaning without dead
paths/lines.

### Acceptance criteria
1. Both token greps return zero under `web/frontend`.
2. `web/frontend/index.html` untouched; no legacy `index.html:<line>` citations.
3. `bun run lint`, `bunx vue-tsc --noEmit`, `bun run test` (209) all pass.

### Verification method
Run the two `git grep` audits from repo root and the three commands from
`web/frontend/`; confirm exit codes and 209 passing tests.

### Constraints
- Comments/tests/docs only — no runtime behaviour change.
- One focused change. Do not delete `web/static/**` or edit `web/server.py`.
- Do not commit/amend/push; do not run `bun run build`/Playwright.
