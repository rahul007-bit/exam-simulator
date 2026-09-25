# DISPATCH — FE-002

## 2026-09-10T06:02:32Z
You are assigned task **FE-002** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-002-opencode`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`web/frontend/src/assets/styles/tokens.css` + `base.css` implementing the slate+indigo
palette, radii, spacing, type, elevation, and the `data-theme` switch, plus the minimal
wiring required for a persisted manual toggle.

### Acceptance criteria
1. all palette values exposed as CSS variables; no raw hex in components
2. dark and light themes both render with AA-contrast text
3. `prefers-color-scheme` default + persisted manual toggle

### Verification method
- `rg '#[0-9a-fA-F]{3,6}' src/components src/views` (no matches)
- `bun run test` (token palette + contrast + hex-audit + theme-toggle suites)
- `bun run build && bun run lint && bunx tsc --noEmit`
- Independent verifier re-runs on a clean checkout / platform host, ideally including the
  Playwright spec `tests/e2e/theme.spec.ts` once browsers are installed.

### Constraints
- One focused change.
- Preserve parity behaviour (WS, clipboard, timer, token routing) — untouched here.
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.
