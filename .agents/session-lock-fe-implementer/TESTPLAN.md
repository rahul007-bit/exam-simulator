# TESTPLAN — session-lock-fe

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | unit | `bun run test` (`session-lock.test.ts` → "creates and persists…") | `cka_client_id` cookie set, equals `getClientId()` | PASS | |
| T2 | unit | `bun run test` ("keeps an existing…") | existing cookie reused unchanged | PASS | |
| T3 | unit | `bun run test` ("sends X-Client-Id…") | header present + `credentials:'include'` | PASS | |
| T4 | unit | `bun run test` ("isLocked") | true only for `{active:false,locked:true}` | PASS | |
| T5 | type | `bunx vue-tsc --noEmit` | no type errors (augmented `SessionInactive`) | PASS | |
| T6 | lint | `bun run lint` | no eslint errors | PASS | |
| T7 | e2e | `npx playwright test` | 20/20; webServer proxy `127.0.0.1:9` | PASS | |

## Edge cases / additions
- `crypto.randomUUID` absent → fallback hex id (covered structurally; jsdom path).
- Locked payload is HTTP 200, not an error (store treats it as state, not `error`).
- `reuseExistingServer:false` proves a live dev server can never be reused.

## Environment
- Commit / build: working tree, branch `feature/frontend-vue-migration`
- Host: Windows (win32), local
- Browser(s): Playwright chromium

## Verdict
- Implementer: PASS, 2026-09-11
- Verifier: pending
