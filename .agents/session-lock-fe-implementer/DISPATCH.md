# DISPATCH — session-lock-fe

## 2026-09-11 (UTC)
You are assigned task **session-lock-fe** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/session-lock-fe-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Frontend owner-lock: per-browser client-id cookie/header; candidate-token resume;
locked-session UI; Playwright webServer hardening; unit tests.

### Acceptance criteria
1. `cka_client_id` cookie ensured (non-HttpOnly, `path=/`, `SameSite=Lax`, 1y) and
   `X-Client-Id` added to every `apiRequest`; `getClientId()` exported.
2. Candidate token stored in `cka:candidate-token`; `initAppStores` and
   `CandidateView` resume with it; cleared on successful submit/reset/end.
3. `SessionInactive.locked?` type; store `isLocked`; `CandidateView` locked card
   (`data-testid="session-locked"`) with Retry; workspace hidden while locked.
4. `playwright.config.ts` `reuseExistingServer: false` and
   `webServer.env.VITE_BACKEND = E2E_BACKEND ?? http://127.0.0.1:9`.
5. `tests/unit/session-lock.test.ts` covers cookie + `isLocked`; all tests green.

### Verification method
From `web/frontend/`: `bun run lint`, `bunx vue-tsc --noEmit`, `bun run test`,
`npx playwright test` (20/20; webServer proxy errors show `127.0.0.1:9`).

### Constraints
- One focused change. Do NOT touch `web/server.py` (concurrent agent) or components.
- Preserve token routing / WS / clipboard / timer parity.
- Update `EVIDENCE.md` with proof.
