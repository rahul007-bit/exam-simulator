# DISPATCH - FE-004

## 2026-09-10T07:34:00Z
You are assigned task **FE-004** (re-claim after verifier rejection) on branch
`feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-004-implementer-3`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Correct `web/frontend/openapi.json` `AdminSessionItem` to match the union of rows
returned by `web/server.py::admin_list_sessions` (lines 1353-1436), then regenerate
`src/api/schema.d.ts`.

Required:
- ADD `container_running` (boolean)
- ADD `current_index` (integer|null)
- ADD `type` (string; enum `active`|`invite`|`archived`)
- ADD `url` (string|null)
- REMOVE `time_limit_minutes`
- CHANGE `total_tasks` to integer|null
- Make all other row fields nullable only where the handler can emit null.
- Optional: add `400` to `/api/session/restore` documented responses.

### Acceptance criteria
1. types generated from /openapi.json
2. client covers session, timer, presets, actions endpoints
3. stores expose typed state and actions; smoke test hits /api/session

### Verification method
`bun run gen:api && bun run typecheck`, `bun run test`, `bun run lint`, `bun run build`
(host equivalent of `npm run gen:api && npx tsc --noEmit` + `npm run test`).

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.
