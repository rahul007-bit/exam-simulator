# TESTPLAN — FE-033

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-033` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | e2e | `bun run test -- tests/unit/admin-invites.test.ts` (browser leg DEFERRED) | invite created via the form for its preset; copyable absolute URL; error surfaced — "invited start screen for its preset" by-equivalent | PASS (Vitest + jsdom; 13/13). Browser leg **DEFERRED** (host-only per PROTOCOL §6) | pending |

### T1 detail (by-equivalent, browser DEFERRED)
The literal browser leg ("create invite and open URL → invited start screen for its
preset") requires Playwright on the platform host (PROTOCOL §6). Locally the same
intent is covered by:

- `useAdminInvites` calls `createSessionInvite(preset)` (POST `/api/admin/sessions/create`)
  and stores the returned `{ token, preset, url }`.
- `AdminInviteForm` renders the preset options (including the synthetic
  `all`/Full Curriculum option passed from `AdminView`), emits `create` with the
  selected preset, and renders the absolute copyable URL, emitting `copy`.
- `buildInviteUrl` composes `${window.location.origin}/?token=…` (already-absolute
  URLs pass through), matching the legacy `admin.js:356` URL routing so the
  generated link opens the candidate start screen for its preset.
- The failure path surfaces the `ApiError` message (simulated 429) and stores no
  invite; `AdminView` toasts it non-blockingly.

## Edge cases / additions
- Empty preset selection → `createInvite()` is called with `undefined` (request
  body `{}`), so the backend applies its default preset.
- Already-absolute `url` passthrough (`https://…`) is not re-prefixed with origin.
- A later create failure clears a previously shown invite (no stale link).
- Clipboard helper writes via `navigator.clipboard.writeText`; empty text is a no-op.
- Non-blocking behavior: existing FE-036 per-row pending state is untouched;
  invite creation has its own `creating` flag and does not gate the sessions table.

## Environment
- Commit / build: e0fb4a3f62a9c57eef2d318534d8c016f5e0fc6d (working tree; `web/frontend/**` untracked)
- Host: win32, branch `feature/frontend-vue-migration`, Bun 1.x / Vitest 3.2.7 + jsdom
- Browser(s): n/a locally (Playwright host-only; DEFERRED to FE-V4)

## Verdict
- Implementer: PASS, 2026-09-10T15:18:31Z
- Verifier: pending
