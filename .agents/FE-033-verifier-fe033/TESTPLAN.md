# TESTPLAN — FE-033

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-033` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | browser: create invite and open URL (host-only) → **DEFERRED**; by-equivalent `bun run test -- tests/unit/admin-invites.test.ts` | invite created for its preset; copyable absolute URL; 429 surfaced | PASS (Vitest+jsdom 13/13; browser DEFERRED) | **PASS** (independently reproduced 13/13; browser leg **DEFERRED** per PROTOCOL §6) |

### T1 detail (by-equivalent, browser DEFERRED)
The literal browser leg requires Playwright on the platform host (PROTOCOL §6).
Locally the same intent is covered and was independently re-run:
- `useAdminInvites.createInvite` calls `createSessionInvite(preset)` (POST
  `/api/admin/sessions/create`) and stores `{ token, preset, url }`.
- `buildInviteUrl` composes `${window.location.origin}${url}` so the generated
  link opens the candidate start screen for its preset (legacy `admin.js:356`).
- A simulated `ApiError(429, …)` is recorded and rethrown, `latestInvite` is
  cleared (no stale link), and `AdminView` toasts it non-blockingly.

## Edge cases / additions
- Empty preset → composable calls `createSessionInvite(undefined)`; `admin.ts`
  sends body `{}` so the backend applies its default preset.
- Already-absolute `url` (`https://…`) passes through without re-prefixing.
- Missing leading slash on a relative path gets a `/` separator.
- Later create failure clears a previously shown invite.
- `copyTextToClipboard` uses `navigator.clipboard.writeText`; empty text is a
  no-op returning `false`.
- Non-blocking: invite `creating` flag is independent of the FE-036 per-row
  session pending state.

## Environment
- Commit / build: HEAD `e0fb4a3` (working tree; `web/frontend/` untracked)
- Host: win32, branch `feature/frontend-vue-migration`, Bun 1.x / Vitest 3.2.7 + jsdom
- Browser(s): n/a locally (Playwright host-only; **DEFERRED** to FE-V4 gate)

## Verifier commands (independent)
```
bun run lint                    -> exit 0
bunx vue-tsc --noEmit           -> exit 0
bun run test -- tests/unit/admin-invites.test.ts -> 1 file / 13 tests passed
bun run test                    -> 17 files / 189 tests passed (baseline 176 + 13)
bun run build                   -> exit 0 (vite built in 5.25s)
```

## Verdict
- Implementer: PASS, 2026-09-10T15:18:31Z
- Verifier: **PASS**, 2026-09-10T15:22:26Z — no failures; browser e2e legitimately
  deferred per PROTOCOL §6 (must run at the FE-V4 gate).
