# DISPATCH — FE-001

## 2026-09-10
You are assigned **FE-001: Vite + Vue 3 + TS scaffold and tooling** on branch
`feature/frontend-vue-migration`.

Working directory: `.agents/FE-001-opencode`
Project workspace: `C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`web/frontend/` scaffold: Vite, Vue 3, TypeScript, ESLint/Prettier, Vitest,
Playwright, dev proxy for `/api`, `/ws`, `/novnc`, build output to `web/dist/`.

### Acceptance criteria
1. `npm run build` succeeds and emits `web/dist/`.
2. `npm run dev` starts and `/api` proxy reaches FastAPI on `:3000`.
3. ESLint + Prettier + `tsc --noEmit` pass.
4. Vitest smoke test passes.

### Verification method
Run every test in `tasks.json` → FE-001 `tests` and `TESTPLAN.md` on a clean,
Node-enabled checkout.

### Constraints
- No UI migration yet (blank app only).
- Build output goes to `web/dist/`, not committed (D-005).
