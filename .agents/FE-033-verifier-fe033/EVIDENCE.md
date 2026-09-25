# EVIDENCE — FE-033

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-fe033 (2026-09-10T15:18:31Z)
- Summary only; the verifier did **not** trust this. See implementer workspace
  `.agents/FE-033-implementer-fe033/EVIDENCE.md`.
- Claimed deliverable: admin "create candidate invite" card + composable + tests.
- Claimed commands: `bun run test` 189/189 (17 files), `bun run lint` clean,
  `bunx vue-tsc --noEmit` clean, targeted `admin-invites` 13/13.

## Verifier — verifier-fe033 (2026-09-10T15:22:26Z)
- Environment: `win32`, branch `feature/frontend-vue-migration`, HEAD `e0fb4a3`,
  working tree; `web/frontend/` is entirely **untracked** (`?? web/frontend/`), so
  the implementer's diff cannot be isolated via git. Bun + Vitest 3.2.7 + jsdom.
  No Playwright browser locally (host-only per PROTOCOL §6).
- Re-ran acceptance commands from `web/frontend/` (all reproduced independently):
  ```
  $ bun run lint
  $ eslint .
  LINT_EXIT=0

  $ bunx vue-tsc --noEmit
  TSC_EXIT=0   (no output)

  $ bun run test -- tests/unit/admin-invites.test.ts
   ✓ tests/unit/admin-invites.test.ts (13 tests) 141ms
   Test Files  1 passed (1)
        Tests  13 passed (13)
  TARGETED_EXIT=0

  $ bun run test
   Test Files  17 passed (17)
        Tests  189 passed (189)
  FULL_EXIT=0

  $ bun run build        # node scripts/gen-api.mjs && vue-tsc --noEmit && vite build
   ✓ 353 modules transformed.
   ../dist/assets/index-*.css / index-*.js + index.html emitted
   ✓ built in 5.25s
  BUILD_EXIT=0
  ```
- Baseline regression check: baseline was 176 tests; new suite adds 13 → 189.
  All 17 files green, so **no previously-green test regressed**. The pre-existing
  `hex-audit` and `decor-audit` unit tests (part of the full run) pass unchanged.
- Test cases re-run independently (see TESTPLAN.md): **T1 PASS** (Vitest + jsdom
  by-equivalent; browser leg **DEFERRED**, see below).
- Criterion-by-criterion result:
  1. **Invite created via `POST /api/admin/sessions/create` (optional preset)** —
     PASS. `useAdminInvites.createInvite(preset?)` calls the typed
     `createSessionInvite(preset)` (`src/api/admin.ts:49`), which POSTs
     `/api/admin/sessions/create` with `{}` or `{ preset }`. `AdminInviteForm`
     emits `create` with the selected preset; `AdminView.onCreateInvite` forwards
     `preset || undefined` (empty → backend default). Backend contract verified at
     `web/server.py:1326-1345` (preset optional, `req.preset or default`).
     Tests: "POSTs the chosen preset…", "omits the preset…", form "emits create
     with the selected preset".
  2. **Generated URL copied to clipboard with toast feedback** — PASS.
     `AdminView.onCreateInvite` builds the absolute URL with `buildInviteUrl`
     (`window.location.origin` + server `url`) and calls `copyTextToClipboard`
     (async Clipboard API → `fallbackCopyText`), then toasts
     `Candidate link generated & copied!`. The output box shows the absolute URL
     and a Copy button that toasts `Invite link copied to clipboard!`. Legacy
     parity: `web/static/js/admin.js:356,365,375`. Tests: absolute-URL helpers,
     `copyTextToClipboard` writes via `navigator.clipboard.writeText`, form
     renders the absolute URL + emits `copy`.
  3. **Capacity-limit / API errors surfaced without a blocking native dialog; no
     stale invite** — PASS. `apiRequest` throws `ApiError` whose `.message` is the
     server `detail` (429 text, `src/api/client.ts:76-100`); `createInvite` stores
     it in `error`, sets `latestInvite = null`, and rethrows; `AdminView` toasts
     it non-blockingly (`Could not create invite: …`) — no native `alert()`.
     Tests: "surfaces a capacity-limit error and does not store an invite",
     "clears a previously stored invite when a later create fails".
- Source review / audits:
  1. **No raw hex** in the new `src/components/admin/AdminInviteForm.vue` or
     `src/views/AdminView.vue` (manual regex scan: 0 matches); the repo
     `hex-audit` test (audits `src/components` + `src/views`, includes both)
     passes in the full run.
  2. **No emoji/glow** in `AdminInviteForm.vue` (read in full: token utility
     classes only; no `text-shadow`/`drop-shadow`/`blur`/gradient/`@keyframes`,
     no pictographs). `decor-audit` scope is `components/ui/**` + a fixed list,
     so it does not cover the new admin component — manual review done instead.
  3. **No native `alert()`/`confirm()`** in any of the three new/changed files.
     `AdminView` uses the promise-based `useConfirm` for session actions
     (pre-existing) and the async `useToast` for invite errors. The only regex
     hits were the words "confirm" in comments and external `useConfirm`, not
     native dialogs.
  4. **Out-of-scope edits:** none attributable to FE-033. The tracked working-tree
     modifications (`web/server.py`, `web/static/*`, `core/*`, `docker/*`,
     `tools/*`) pre-date this verification and are unrelated platform work;
     FE-033's four artifacts live entirely under untracked `web/frontend/`.
- Test-quality review: tests are substantive, not tautological — they mock the
  real `@/api/admin` module, assert the exact preset argument, assert
  `ApiError`/429 propagation and state clearing, assert absolute-URL composition
  from `window.location.origin`, and assert real clipboard writes + component
  emits. **Residual gap (non-blocking):** the suite mocks `createSessionInvite`
  so `admin.ts`'s literal endpoint/body conversion is not directly asserted, and
  the `AdminView` toast-on-create/copy wiring is not unit-asserted (covered by
  the `toast` suite + the form/composable tests). Not a false or weak assertion.
- E2E deferral: T1 in `tasks.json` is an **e2e** case ("create invite and open
  URL → invited start screen for its preset"). No admin-invite Playwright spec
  exists; PROTOCOL §6 explicitly permits "PASS-by-equivalent + browser DEFERRED"
  when the browser is host-only, to be resolved at the milestone gate. The
  Vitest/jsdom equivalent is legitimate and must be run for real at FE-V4.
- Verdict: `verified` — all three acceptance criteria reproduced independently;
  lint/typecheck/build green; 189/189 unit tests pass with no regressions; browser
  e2e legitimately DEFERRED per PROTOCOL §6.
