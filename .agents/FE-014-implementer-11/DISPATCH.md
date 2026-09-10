# DISPATCH — FE-014

## 2026-09-10
You are assigned task **FE-014** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-014-implementer-11`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Remove glows/pulse/badgePop and any decorative animations/shadows that violate D-003;
remove emoji from UI copy; add an inline-SVG `Icon` component covering the glyphs
currently used (toast variants, close, etc.).

### Acceptance criteria
1. no box-shadow glow, no text-shadow, no decorative keyframes
2. no emoji in UI copy
3. icon set covers all current glyph needs
4. existing tests still pass

### Verification method
- `bun run test` (includes the new `tests/unit/decor-audit.test.ts`)
- `bunx tsc --noEmit`
- `bun run lint`
- grep audit for glow/shadow/blur/gradient/emoji over the owned sources

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; the orchestrator owns `tasks.json` in the batch.
