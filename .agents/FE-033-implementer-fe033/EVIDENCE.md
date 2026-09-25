# EVIDENCE — FE-033

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-fe033 (2026-09-10T15:18:31Z)
- Deliverable: Admin "Create candidate invite" surface — create a session invite
  (optional preset) and copy the generated absolute URL to the clipboard with
  toast feedback; capacity/API errors surfaced non-blockingly.
- Files touched:
  - `web/frontend/src/composables/useAdminInvites.ts` (new)
  - `web/frontend/src/components/admin/AdminInviteForm.vue` (new)
  - `web/frontend/src/views/AdminView.vue` (modified)
  - `web/frontend/tests/unit/admin-invites.test.ts` (new)
  - `.agents/FE-033-implementer-fe033/*` (workspace docs)
- No shared/out-of-scope files changed (no `web/server.py`, `web/static/**`, configs,
  router, `package.json`, `openapi.json`, `tests/setup.ts`).

- Commands run + output (from `web/frontend/`):
  ```
  $ bun run test -- tests/unit/admin-invites.test.ts
   ✓ tests/unit/admin-invites.test.ts (13 tests) 140ms
   Test Files  1 passed (1)
        Tests  13 passed (13)

  $ bun run lint
  $ eslint .

  $ bunx vue-tsc --noEmit
  (no output — typecheck clean)

  $ bun run test
   Test Files  17 passed (17)
        Tests  189 passed (189)
  ```
- Screenshots: n/a (no browser in this environment; host-only leg deferred)
- Test cases executed (see TESTPLAN.md): T1 PASS (by-equivalent, Vitest + jsdom;
  browser leg DEFERRED per PROTOCOL §6)
- Self-check against acceptance criteria:
  1. Invite created via `/api/admin/sessions/create` — PASS. `useAdminInvites.createInvite`
     calls the typed `createSessionInvite(preset)`; `AdminInviteForm` emits the
     selected preset from the reused `presetOptions` (`AdminView` passes `all`/
     Full Curriculum too). Unit: "POSTs the chosen preset and stores the returned invite",
     "omits the preset when none is selected", `AdminInviteForm` "emits create with the
     selected preset".
  2. URL copied with toast feedback — PASS. `AdminView.onCreateInvite` builds the
     absolute URL via `buildInviteUrl` and copies through `copyTextToClipboard`
     (async Clipboard API + `fallbackCopyText` fallback), then toasts
     `Candidate link generated & copied!` (legacy parity). The output box renders the
     absolute copyable URL and a Copy link button that toasts
     `Invite link copied to clipboard!`. Unit: URL helpers + `copyTextToClipboard`
     (writes with `navigator.clipboard.writeText`) + form "renders the copyable absolute
     URL and emits copy".
  3. Capacity-limit / API errors surfaced — PASS. `apiRequest` throws `ApiError` whose
     `.message` is the server `detail` (429 text); `createInvite` records it in `error`,
     clears `latestInvite`, and rethrows; `AdminView` toasts it non-blockingly
     (`Could not create invite: …`). Unit: "surfaces a capacity-limit error and does not
     store an invite" + "clears a previously stored invite when a later create fails".
- Regression notes: full suite 189/189; hex/decor audits pass (token utilities only);
  FE-036 non-blocking sessions behavior untouched (separate `creating` state).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS, T2 FAIL, ...>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
