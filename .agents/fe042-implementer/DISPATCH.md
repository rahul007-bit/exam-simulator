# DISPATCH — FE-042

## 2026-09-11T07:15:25Z
You are assigned task **FE-042** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/fe042-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Playwright E2E specs for the candidate journey (`/` start → workspace →
question-nav jump → submit scorecard) and the admin journey (`/admin` sessions
table, config/resource forms, row action, create invite), plus an axe-core
accessibility scan over `/`, an open modal and `/admin`. Add a dependency-free
`helpers.ts` with the shared offline API/WebSocket/noVNC/fullscreen mocks.

### Acceptance criteria
1. E2E covers candidate + admin critical paths.
2. axe reports no critical violations.
3. Runs headless in CI/local.

### Verification method
Host-only (PROTOCOL §6), run from `web/frontend/` after the orchestrator starts
the dev server (`bun run dev`, which `reuseExistingServer` picks up):
- `npx playwright test` → all journeys pass (T1)
- `npx playwright test tests/e2e/a11y.spec.ts` → no critical axe violations (T2)

Local (non-browser) checks performed by the implementer:
- `bunx vue-tsc --noEmit`
- `bun run lint`

### Constraints
- One focused change (new E2E specs + helpers only).
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; set status in `tasks.json` (orchestrator).
