# BRIEFING — FE-042

## Mission
Deliver Playwright E2E journeys for the candidate and admin critical paths plus
an axe-core accessibility audit, all deterministic and offline (mocked backend),
to close out the Phase 4 cutover verification for the Vue migration.

## 🔒 Identity
- Task: FE-042
- Role: implementer
- Working directory: .agents/fe042-implementer
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-040
- **Acceptance criteria:**
  1. E2E covers candidate + admin critical paths
  2. axe reports no critical violations
  3. runs headless in CI/local
- **Test cases:** (also in `tasks.json`)
  1. T1 `npx playwright test` (host-only) → all journeys pass
  2. T2 `axe scan` (browser, host-only) → no critical violations
- **Verifier:** independent-agent

## Key constraints
- Browser leg (T1/T2) is **host-only** per PROTOCOL §6; the orchestrator runs
  `npx playwright test` once after the batch. Do not run Playwright or
  `bun run build` locally.
- No backend runs locally, so every journey must mock `/api/**` and stub
  `/ws/**` (WebSocket) + noVNC + fullscreen. Keep tests deterministic/offline.
- Do not edit `playwright.config.ts`, `package.json`, `src/**`, other `tests/**`.
- Only new files under `web/frontend/tests/e2e/**`.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Files in scope: `web/frontend/tests/e2e/{candidate-journey,admin-journey,a11y}.spec.ts`, `tests/e2e/helpers.ts`

## Artifact index
- `.agents/fe042-implementer/DISPATCH.md`
- `.agents/fe042-implementer/progress.md`
- `.agents/fe042-implementer/EVIDENCE.md`
