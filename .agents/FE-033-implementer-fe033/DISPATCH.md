# DISPATCH — FE-033

## 2026-09-10T15:18:31Z
You are assigned task **FE-033** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-033-implementer-fe033`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
create session invite (optional preset) with copyable URL

### Acceptance criteria
1. A candidate session invite can be created from the admin UI via `POST /api/admin/sessions/create` (optional preset selection).
2. The generated invite URL is copied to the clipboard and confirmed with a toast.
3. Capacity-limit / API errors (e.g. HTTP 429 "Server resource limit reached…") are surfaced to the admin (toast, non-blocking).

### Verification method
From `web/frontend/`:
- `bun run lint`
- `bunx vue-tsc --noEmit`
- `bun run test`
Plus `tests/unit/admin-invites.test.ts` (13 tests) covering T1 by-equivalent.
Literal Playwright leg is host-only and DEFERRED to FE-V4.

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing).
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.
