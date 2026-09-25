# DISPATCH — FE-004

## 2026-09-10T07:26:19Z
You are (agent **implementer-2**) assigned task **FE-004** on branch
`feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-004-implementer-2`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`src/api` client generated from `/openapi.json` + `src/stores` (session, timer, presets)
with typed responses; wire the stores into the app minimally.

### Acceptance criteria
1. types generated from `/openapi.json`
2. client covers session, timer, presets, actions endpoints (plus admin login as needed)
3. stores expose typed state and actions; smoke test hits `/api/session`

### Verification method
- `bun run gen:api && bun run typecheck` (accepted equivalent of
  `npm run gen:api && npx tsc --noEmit`)
- `bun run test`
- `bun run lint`, `bun run build`, `bun run format:check`

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing); no UI beyond wiring.
- Update `EVIDENCE.md` with proof; set status in `tasks.json` (in-review, not verified).
