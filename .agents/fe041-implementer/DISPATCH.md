# DISPATCH — FE-041

## 2026-09-11 07:13 UTC
You are assigned task **FE-041** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/fe041-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Vendored latin woff2 Inter + JetBrains Mono under `web/frontend/public/fonts/`,
new `src/assets/styles/fonts.css` with `@font-face` rules imported from
`base.css`, and a `tests/unit/offline-audit.test.ts` regression guard.

### Acceptance criteria
1. No runtime CDN calls; Inter + JetBrains Mono + all libs bundled.
2. Network tab shows no external requests; assets served from same origin; offline load renders correctly.

### Verification method
- `bun run lint`
- `bunx vue-tsc --noEmit`
- `bun run test` (expect baseline 209 + 9 new = 218)
- T2 manual: serve `dist/`/dev with network disabled, confirm styled + functional.

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Do not touch package.json, e2e/**, playwright config, components/views, server.py, docs, board files.
- Update `EVIDENCE.md` with proof; do not self-certify.
