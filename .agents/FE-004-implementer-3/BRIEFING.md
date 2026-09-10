# BRIEFING - FE-004

## Mission
Fix the committed OpenAPI snapshot so `AdminSessionItem` matches the
`GET /api/admin/sessions` handler, then regenerate types and re-run the full
gate suite. (Re-claim after verifier rejection of implementer-2.)

## Identity
- Task: FE-004
- Role: implementer (re-claim / fix iteration)
- Working directory: .agents/FE-004-implementer-3
- Branch: feature/frontend-vue-migration

## Task contract
- **Depends on:** FE-003
- **Acceptance criteria:**
  1. types generated from /openapi.json
  2. client covers session, timer, presets, actions endpoints
  3. stores expose typed state and actions; smoke test hits /api/session
- **Test cases:**
  1. T1 `npm run gen:api && npx tsc --noEmit` -> types generate; exit 0
  2. T2 `session store fetchSession()` -> typed /api/session data populated
- **Verifier:** independent-agent (do NOT self-verify)

## Key constraints
- Follow `decisions.md` - no contradicting accepted decisions without a new entry.
- Strict behavioral parity (D-007): preserve WS contracts and URL/token routing.
- Scope: only FE-004 files. Do not commit/push.

## Pointers
- Plan: `.agents/frontend-migration/PLAN.md`
- Protocol: `.agents/frontend-migration/PROTOCOL.md`
- Board: `.agents/frontend-migration/BOARD.md`
- Rejection: `.agents/FE-004-implementer-2/EVIDENCE.md` (Verifier section)
- Files in scope: `web/frontend/openapi.json`, generated `web/frontend/src/api/schema.d.ts`

## Artifact index
- `.agents/FE-004-implementer-3/DISPATCH.md`
- `.agents/FE-004-implementer-3/progress.md`
- `.agents/FE-004-implementer-3/EVIDENCE.md`
- `.agents/FE-004-implementer-3/TESTPLAN.md`
