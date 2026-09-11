# HANDOVER — Frontend Migration (continue this session)

Written: 2026-09-10; **updated: 2026-09-11**. Branch: **`feature/frontend-vue-migration`**
(based on `feature/phase-3-arch`). All work is now **committed** (see §11 for the commit log and the
host deployment). Never commit unless the user asks.

## 1. Mission

Migrate the legacy vanilla-JS frontend to **Vue 3 + TypeScript + Vite** with a professional
slate+indigo design system (dark + light), preserving strict behavioral parity. Full plan:
`.agents/frontend-migration/PLAN.md`; decisions: `decisions.md`.

## 2. Status snapshot

- Board: **32 verified, 14 todo** (46 tasks). `python scripts/agents_board.py --check` is green.
- Verified: `FE-000..005, 010..014, 020..036, FE-040, FE-041, FE-042, FE-043`.
- Remaining todo: `FE-044`, gates `FE-V1..V5`, backlog `FS-001..008`.

### Remaining tasks
| ID | Depends | Title |
|---|---|---|
| FE-044 | FE-042 | Full regression vs real backend (**host-only**) |
| FE-V1..V4 | phase tasks | Milestone independent-verification gates |
| FE-V5 | FE-040..044 | Victory audit |
| FS-001..008 | – | Future backlog (auth, ownership, dashboards, preset builder) |

**Immediate next:** **FE-044** (full regression: candidate exam + admin lifecycle vs the real backend)
then the gates **FE-V1..V5**. FE-044 is host-only; the user is running it against `https://10.8.0.15/`
(§11). The browser/E2E legs now run locally too (Playwright + chromium on the workstation).

## 3. Where everything lives

- Program workspace / rules / board: `.agents/frontend-migration/`
  - `PROTOCOL.md` (§9 = parallel-batch + verification rules — read this first)
  - `PLAN.md`, `decisions.md` (D-001..D-009), `ORIGINAL_REQUEST.md`
  - `tasks.json` (canonical) + `BOARD.md` (generated), `templates/`
  - `scripts/agents_board.py` (CLI: `--check --claim ID AGENT --force REASON --status --set-evidence --verify --unclaim --reject`)
- Frontend app: `web/frontend/` (Vue 3 + TS + Vite, **Tailwind v4** via `@tailwindcss/vite`, `@headlessui/vue`,
  Pinia, vue-router, `@tanstack/vue-table`, xterm, noVNC, marked+DOMPurify+highlight.js, axe-core;
  **self-hosted** Inter + JetBrains Mono woff2 under `public/fonts/`).
- Backend: `web/server.py` serves the built SPA (`web/dist`) with a client-side-routing fallback and
  owns `/admin`; the legacy `web/static` UI was **removed** in the FE-040 cutover, so the built SPA is
  the only UI and the server returns **503** until `web/dist` exists. Build helper
  `tools/build-frontend.sh` (called by `tools/start-web.sh` and the systemd `ExecStartPre`).
- Reverse proxy: **`docker/traefik/`** — Traefik v3 container (host network) terminating TLS on `:443`
  (self-signed), redirecting `:80 → :443`, with a basic-auth dashboard (`/dashboard`) and Prometheus
  metrics (`/metrics`). This makes the origin a **secure context** (required by the Keyboard Lock API).
- Session-lock test: `tests/test_session_owner_lock.py` (stdlib unittest).

### Frontend architecture (Vue 3 + Vite SPA)

- **Stack:** Vue 3 + TypeScript + Vite, **Tailwind v4** (`@tailwindcss/vite`), Headless UI, Pinia,
  vue-router, TanStack Table, xterm (+ fit addon), noVNC (hosted at `/novnc`), marked + DOMPurify +
  highlight.js; axe-core + Playwright/Vitest for tests.
- **Source layout (`web/frontend/src/`):**
  - `views/` — route views (`CandidateView`, `AdminView`, `LoginView`, `DevUiView`, `PlaceholderView`)
  - `components/layout/` — `AppShell`, `AppHeader`, `OverflowMenu`, `WorkspaceSplit`
  - `components/ui/` — design-system primitives (`Button`, `Modal`, `DataTable`, `Select`, `Badge`, ...)
  - `components/candidate/` — `TaskPane`, `QuestionDrawer`, `ExamScorecard`, `RecordingsModal`, ...
  - `components/admin/` — config/resource/invite forms, infrastructure table, `ObserveOverlay`, ...
  - `components/workspace/` — workspace "islands": `XTerm`, `NoVncFrame`, `WorkspaceTabs`,
    `ClipboardBridge`, `ReplayPlayer`
  - `composables/`, `stores/`, `api/` — behavior, Pinia state, typed API clients (generated `schema.d.ts`)
  - `assets/styles/` — design tokens + base styles; `router/`
  - `tests/unit` (Vitest), `tests/e2e` (Playwright)
- **Build-on-deploy:** `web/frontend/` builds to `web/dist/`, which is **git-ignored** (D-005) and
  **never committed**. `tools/build-frontend.sh` (npm, else bun; requires **Node.js >= 20.19 + npm**)
  is invoked by `tools/start-web.sh` and the systemd `ExecStartPre`.
- **Dev:** `cd web/frontend && npm install && npm run dev` (Vite on `:5173`, proxying `/api`, `/ws`,
  `/novnc` to `:3000`). See `web/frontend/README.md`.

## 4. How to work (parallel batch mode — PROTOCOL §9)

The user wants **speed**: up to **3 implementer agents concurrently**, and **testing paused** except when
something is incomplete.

- Orchestrator (you) **pre-claims** the tasks (`python scripts/agents_board.py --claim <id> <agent>`);
  worker agents must **not** run the board CLI during a batch.
- Give each agent a **disjoint file list** + a do-not-touch list. Orchestrator owns shared files
  (`App.vue`, `main.ts`, `router`, `web/frontend/src/views/CandidateView.vue`, `AdminView.vue`, configs).
- During a batch, agents run **only** `bunx vue-tsc --noEmit`. Do **not** run `bun run build` or
  Playwright concurrently (they write `web/dist` / bind port 5173).
- After a batch, the orchestrator runs one consolidated pass: `bun run lint && bunx tsc --noEmit &&
  bun run test && bun run build && npx playwright test`, then marks tasks verified with evidence paths.
- Only run the heavier suite sooner if an agent reports something **INCOMPLETE**.
- Record per-task evidence at `.agents/<task-id>-<agent>/EVIDENCE.md` (+ `TESTPLAN.md`), set via
  `--set-evidence` then `--verify`.

## 5. Commands (frontend)

```bash
cd web/frontend
bun install                 # Bun 1.4.2 is available; npm 11.19.1 also present
bunx vue-tsc --noEmit       # typecheck (.vue included)
bun run lint                # eslint
bun run test                # vitest (currently 230 tests, all green)
bun run build               # gen:api (offline snapshot) + vue-tsc + vite -> web/dist
npx playwright test         # chromium (currently 21 tests); hardened — see note
```
- `bun run build` regenerates the git-ignored `src/api/schema.d.ts` from `web/frontend/openapi.json`
  (a curated snapshot; FE-004). No backend needed to build.
- **E2E is hardened**: `playwright.config.ts` sets `reuseExistingServer:false` and
  `webServer.env.VITE_BACKEND=http://127.0.0.1:9` (dead port) so tests can **never** proxy to a live
  backend. Do not restore a real `VITE_BACKEND` in that config (an earlier reused dev server attached
  to the live session and resized the user's VNC).
- Vitest prints `localStorage is not available...` warnings under Node — benign.

## 6. Environment / host

- Dev happens on this Windows workstation; **Bun 1.4.2**, **npm 11.19.1**, **Node 26** are available.
  Use `bun run ...`; `npx playwright test` works (Playwright 1.63 + chromium installed).
- Linux platform host: **`root@10.8.0.15`** (`exam-standardpc`), FastAPI live on `:3000`, deployed at
  `/root/cka-labs` (**not a git repo**). SSH from this workstation needs the full path:
  `& "$env:SystemRoot\System32\OpenSSH\ssh.exe" ... root@10.8.0.15 "cmd"` (avoid `|`/`$`/`{}` inside
  the remote command — PowerShell mangles them; use `;`, redirects, or `grep -c pat file`).
  - Host has **Node 22** but **npm is not on the default PATH** (Ubuntu split package); `corepack` exists.
  - The VPN path had an MTU black-hole (large/`scp` stalled). The user fixed the OpenVPN DCO MTU;
    `scp`/`tar` deploys work now. If bulk transfer stalls again, it's MTU.
  - **Host-only verification pattern:** copy a modified `web/server.py` alongside a backup, validate with
    `.venv/bin/python -m py_compile web/server.py` and `.venv/bin/python -c 'import web.server'`, then
    restart `k8s-web.service` and probe `curl -sk https://127.0.0.1/`. `python
    scripts/verify_platform_api.py` provisions an Incus fleet — run only when intended (passed once 44/0).
  - **Deployed state (2026-09-11):** the branch SPA (`web/dist`), the owner-lock `web/server.py`, and a
    rebuilt `cka-desktop:latest` image are live; `https://10.8.0.15/` is served through Traefik. See §11
    for rollback artifacts.

## 7. Key architecture / gotchas

- **Design system:** tokens in `src/assets/styles/tokens.css` (do not change values; tests assert them);
  Tailwind `@theme inline` maps them in `base.css`. No raw hex in `src/components`/`src/views`
  (`hex-audit` test), no glow/emoji (`decor-audit` test). Fonts are **self-hosted** (`fonts.css` +
  `public/fonts/*.woff2`); an `offline-audit` test forbids CDN font hosts.
- **Shell:** `App.vue` suppresses the global topbar on the candidate route; `ThemeToggle` lives inside
  the candidate `AppHeader`. `CandidateView.vue` owns the AppShell + `WorkspaceSplit` + `WorkspaceTabs`
  (noVNC/XTerm), with `ClipboardBridge` and `FullscreenGuard` mounted. `TaskPane` has a **footer**
  (Previous · Reset task · Task X of Y · Next) wired to `session.prev()/next()/retry()`.
- **Split pane:** drag the gutter fully left to collapse the left pane; a chevron button toggles it;
  the collapsed state persists (`cka:workspace:split:collapsed`).
- **Admin:** auth guard (FE-030) + `AdminView` (sessions table, config/resource forms, infrastructure
  table — one card, observe overlay). Mutations are **non-blocking / per-row** (FE-036) — keep that.
- **Session owner lock (soft, no auth):** the SPA sets a per-browser `cka_client_id` cookie; the backend
  records `session:{sid}:owner` (Redis, TTL 86400). A different client gets a `locked` `/api/session`
  payload (→ "exam already in progress" screen) and **409** on candidate APIs; `/ws/session`,
  `/ws/terminal`, `/novnc` close **1008**. Admins and **no-cookie** internal callers bypass; the owner is
  released on submit/reset/end/terminate. Refresh resumes by the persisted `cka:candidate-token` +
  cookie. **Soft lock** — clearing storage yields a new id; two tabs in one browser share the cookie.
- **HTTPS is required for strict mode:** the Keyboard Lock API (`navigator.keyboard`) only exists in a
  **secure context** — `https://` or `http://localhost`. Plain `http://10.8.0.15:3000` silently disables
  keyboard lock (Esc exits fullscreen, Alt+Tab escapes). Traefik provides the HTTPS origin; the cert is
  self-signed (browser warning once).
- **Vite dev proxy** logs `ECONNREFUSED` for `/api/*` because no backend is local — **benign**.
- **Board CLI** requires evidence before `in-review`/`verified`; `--claim` enforces the dep gate.
- **Do not restore** the deleted legacy `web/static` UI. (A past subagent deleted `ansible/*.cfg|ini`;
  it was restored — use `git restore` if it recurs.)

## 8. Known integration gaps / TODOs

- Overflow action `new-tab` is still a no-op in `CandidateView.onAction`; `reload` **is** wired
  (terminal reconnect / noVNC reload via `WorkspaceTabs`).
- FE-042's literal browser legs were DEFERRED during the terse batches but now **run locally**
  (`npx playwright test` → 21 passing). The milestone gates re-run Playwright + axe.
- **Still open:** a live timer in the observe overlay; Chromium-based browsers are not tracked
  (Firefox only); the Traefik dashboard uses a self-signed cert and a basic-auth password that should be
  rotated (it was surfaced during the deploy session).
- FE-044 (host regression) and gates FE-V1..V5 remain.

## 9. Suggested next actions

1. `python scripts/agents_board.py --check`
2. Run **FE-044** (full exam + admin lifecycle vs the real backend) against `https://10.8.0.15/`, then
   the gates **FE-V1..V5** (independent verification; Playwright + axe locally).
3. Consider filing the post-verification parity fixes from §10/§11 as `FE-0xx`/`FS` tasks so the gates
   re-cover them.

## 10. Session 1 fixes (2026-09-10; historical — now committed via §11)

These were raised by the user while exercising the SPA against the live platform host. They are
**parity gaps** (the board's acceptance criteria were narrower than the legacy behaviour).

### Frontend (`web/frontend`)
- **Admin page couldn't scroll** — `App.vue` locked every route to `height:100vh; overflow:hidden`.
  Made the fixed shell conditional (`app-shell--fixed`, candidate route only); admin/login now scroll.
  Also made `showTopbar` null-safe (`route?.name`) — the unit smoke test mounts without a router.
- **Preset modal** — removed the inherited `ul` left padding (symmetric insets) and styled the list
  scrollbar (`PresetModal.vue`).
- **Candidate header** — a dedicated `warning` Button variant (added to `ui/types.ts` + `Button.vue`);
  Flag now uses it instead of danger; the progress/task-list button is a real button (`secondary`);
  the session ID is shown beside it as a click-to-copy chip (emits `copy-session-id` → `CandidateView`).
- **Clipboard (FE-027 parity)** — `ClipboardBridge` connected once to `/ws/session/active` before the
  store hydrated and never rebound. It now watches `[sessionId, active]` and reconnects. Also `TaskPane`
  re-emits the markdown code-copy event and `CandidateView` mirrors it into the desktop via `sendToVnc`.
- **Observe overlay (FE-035 parity)** — added the task-instructions pane (badges + sanitized markdown),
  the "All tasks in exam" list, a **Review & replay** button, and a resizable left pane reusing
  `WorkspaceSplit` (`cka:observe:split`). Lowered the overlay from `z-[1100]` to `z-[900]` so global
  dialogs/toasts (z-1000) are above it.
- **Replay UI (modernised, not a legacy replica)** — wide `xl` modal, timeline left (Events/Tasks,
  click-to-seek) and large terminal right, transport with `-10s`/`+10s`/Restart/Speed (`ReplayPlayer.vue`,
  `RecordingsModal.vue`). `showList`/`showEvents`/`initialSessionId` props scope the admin/observe review
  to one session; added a visible **Close**. Distinct Badge colour per event type.
- **Crash fix (important)** — `Select.vue` (Headless UI `Listbox`) threw `Passing props on "template"!`
  when any extra attr (e.g. `aria-label`) was passed, killing the whole Vue render. Fixed with
  `inheritAttrs:false` + `v-bind="$attrs"` on the `ListboxButton`.
- **Manage session dialog** — actions are a 2-column grid and gained **Review & replay**.
- **Candidate start feedback** — the start screen shows a loading button + live status line.
- **Global scrollbars** — slim token-coloured scrollbars in `base.css`.

### Backend (tracked)
- **`core/recorder.py`** — `_find_places_db` also searches Snap/Flatpak Firefox profiles, honours
  `FIREFOX_PROFILE_DIR`, prefers the most-recently-used profile, and (with `RECORDER_DEBUG=1`) warns
  once when none is found.
- **`docker/desktop/desk-agent.py`** — the browser runs **inside the desktop container**, so the
  host-side poller can never see its Firefox profile. Added `start_browser_history_poller` in the
  sidecar (reads the container-local `places.sqlite`, publishes `BROWSER_NAVIGATE`/`BROWSER_SEARCH` to
  `events:{session_id}`) and suppressed `WINDOW_FOCUS` for browser windows.

## 11. Session 2 (2026-09-11) — commits, delivered fixes, deployment

### Commit log (local; no remote configured)
```
ebd3f62 feat(infra): add Traefik HTTPS reverse proxy with dashboard and metrics
85b95af feat(candidate): single-client session lock, token resume, and task navigation
4789371 feat(frontend): self-host fonts, add Playwright E2E + axe, and refresh docs
79297c8 feat(cutover): remove legacy web/static UI and serve only the built SPA
47471ad chore: remove obsolete scratch scripts and stale root docs
28ebcb8 fix(platform): harden fleet lifecycle, desktop input and browser-history capture
3ccd177 feat(frontend): migrate UI to Vue 3 + TypeScript + Vite SPA
```

### Board tasks completed this session
- **FE-033** admin create invite (verified) — unblocked FE-040.
- **FE-040** legacy removal + static cutover (verified): `web/static` deleted, server serves only
  `web/dist`, strict legacy-reference purge, `tests/test_frontend_cutover.py`.
- **FE-041** self-host fonts (verified): Inter + JetBrains Mono woff2 + `fonts.css` + `offline-audit`.
- **FE-042** Playwright E2E + axe (verified): candidate/admin journeys + a11y (zero critical) — now 21 tests.
- **FE-043** docs (verified): README/PLATFORM_SETUP/handover/frontend README.

### Post-verification UI fixes (parity gaps; no board ids)
- **DataTable** — rows-per-page selector, fixed-height scroll with sticky header, visible "Rows per page"
  text removed, and Sessions search now matches the **session id** (`accessor` added to `DataTableColumn`).
- **Candidate badges** — click-to-copy + accent styling (TaskPane/QuestionDrawer/scorecard/recordings);
  `@keydown.stop` to avoid nested-card navigation; `context:`/`ns:` chips copy the raw value.
- **Candidate Reload** — overflow action reconnects the terminal or reloads the noVNC frame.
- **Infrastructure** — removed the duplicate outer card (single "Fleet infrastructure" card).
- **Candidate nav parity** — TaskPane footer (Previous/Reset/Next) and the QuestionDrawer now refetches
  `/api/questions` on every open (so a jump is reflected). Fixed the VNC-resize-during-tests issue by
  hardening the Playwright config.

### Session owner lock (new)
See §7. Backend enforcement in `web/server.py`; frontend client id / resume / locked screen; tests:
`tests/test_session_owner_lock.py` (11), `web/frontend/tests/unit/session-lock.test.ts`,
`web/frontend/tests/e2e/session-locked.spec.ts`.

### Host deployment (`root@10.8.0.15`)
- Deployed `web/dist` + owner-lock `web/server.py` to `/root/cka-labs/`; restarted `k8s-web.service`
  (`active`); `https://10.8.0.15/` and `/admin` return 200.
- **Traefik** (`docker/traefik/`): HTTPS on `:443` (self-signed cert, SAN `10.8.0.15`), `:80 → :443`,
  dashboard at `/dashboard/` (basic auth `admin`), metrics at `/metrics`. Rollback:
  `cd /root/cka-labs/docker/traefik && docker compose down`. Dashboard creds live in
  `/root/cka-labs/docker/traefik/users.txt` (apr1 hash) — **rotate** (they were surfaced this session):
  `rm users.txt && DASH_PASS='new' ./setup.sh`.
- **Desktop image** rebuilt: `cka-desktop:latest` now bakes the updated `desk-agent.py` (browser-history
  poller). Rollback tag: `cka-desktop:pre-hist`.
- **Rollback artifacts on the host:** `/tmp/server.py.orig` (pre-FE-040), `/tmp/server.py.prelock`
  (pre-owner-lock), `/tmp/desk-agent.py.orig`, `/tmp/entrypoint.sh.orig`.

### New open items
- Rotate the Traefik dashboard password (above).
- FE-044 + gates FE-V1..V5 still pending.
- Observe-overlay live timer; Chromium browser tracking (Firefox only).
- **NEEDS DISCUSSION: vendor noVNC into the SPA.** The noVNC *client* static
  files are currently a host apt dependency (`/usr/share/novnc`, mounted in
  `web/api/__init__.py`). Proposal: copy the noVNC dist into
  `web/frontend/public/novnc/` so it ships inside the SPA build — drops
  `NOVNC_DIR`, removes the node-local static dependency, aligns with the
  self-hosted fonts/offline philosophy and the k8s end goal. Iframe URLs
  (`/novnc/vnc.html?...`) would keep working unchanged. Not done yet — user
  wants to discuss first.

## 12. Session 3 (2026-09-11) — backend modularization (off-board)

The user decided to modularize the backend **before** the FS backlog, with the
end goal of Docker/Kubernetes deployment (module boundaries = future service
boundaries). Plan: `.agents/backend-modularization/PLAN.md`.

- `web/server.py` (2,542 lines) split into the **`web/api/` package**:
  `state/schemas/security/owner_lock/candidate_tokens/desktop_restore/
  presets_info/clipboard_state/exam_helpers` + `services/
  {session_view,submit}` + `background.py` + `routes/{session,exam,presets,
  clipboard,recordings,admin,ws_terminal,ws_desktop,ws_events,spa}`.
- `web/server.py` is now a thin **facade**: `app = create_app()`; keeps the
  `uvicorn.run("web.server:app")` contract (`core/cli.py:481`).
- Route imports are **lazy** inside `create_app()` so single route modules are
  importable on non-host platforms (tests import `web.api.routes.recordings`
  without pulling pty/fcntl).
- Option-2 state moves: `_selected_preset_override` → Redis `preset:override`
  (+ in-memory fallback); admin-token and candidate-token in-process maps kept
  only as fast-path caches over their Redis source of truth.
- Tests updated: `test_session_owner_lock` → parses `web/api/owner_lock.py`;
  `test_recorder` imports recording endpoints from `web.api.routes.recordings`
  + `web.api.schemas`; `test_frontend_cutover` SPA assertions → `spa.py`.
- Fixed pre-existing bug: `core/desktop_manager.py` used `List[...]` without
  importing `List` (broke `import web.server` at HEAD everywhere).
- `.gitignore`: added `recordings/`, `reports/` (runtime output).
- Local verification: `py_compile` all modules OK; Python unit tests 19 pass /
  1 skip / 3 pre-existing host-only failures (termios, k3d binary, Firefox
  profile — unrelated to the refactor).
- **Deployed to host (2026-09-11):** `web/api/`, facade `web/server.py`, and the
  `desktop_manager.py` fix copied to `/root/cka-labs/`; `k8s-web.service`
  restarted (`active`); startup clean (111 questions pre-warmed); probed 200:
  `/`, `/admin`, `/api/session`, `/api/timer`, `/api/presets`,
  `/api/admin/check`, `/api/recordings`. Two deploy-time catches: host FastAPI
  has no `add_event_handler` (startup hook via `@app.on_event` instead) and
  route handlers must keep `request: Request` annotations (bare `request`
  becomes a query param → 422). Rollback artifacts: `/tmp/server.py.premod`,
  `/tmp/desktop_manager.py.premod` (restore file, restart service).

### FS batch 1 (2026-09-11, verified on board)
- **FS-001 auth backend** — `web/api/users.py` (Redis user store, pbkdf2_sha256
  390k iters, `ensure_bootstrap_admin` from env at startup), `web/api/
  auth_sessions.py` (`cka_auth_token` cookie / Bearer, `auth:session:{token}`
  TTL 7d), `routes/auth.py` (`/api/auth/login|logout|me`, admin user
  management), `is_admin_authenticated` now also accepts auth sessions with
  role "admin". Tests: `tests/test_auth_users.py` (23 pass / 6 host-only skip).
- **FS-006 preset generator API** — `web/api/services/preset_generator.py`
  (validation + enum mapping → `QuestionSelector.select_custom`) +
  POST `/api/presets/generate` (starts session via the start_exam pattern,
  response never lists questions). Tests: `tests/test_preset_generator.py`
  (12 pass).
- Design decisions recorded as **D-010** (Redis users, stdlib pbkdf2, Redis
  session cookie; catalog enumeration admin-only at API level — feeds FS-008;
  `GET /api/presets` stays public until FS-008).
- **Not deployed to the host yet** — deploy together with the next batch or
  before FE-044 (host-only endpoint tests for auth should run then).
- **Unblocked next:** FS-002 (auth frontend — update `web/frontend/openapi.json`
  snapshot first, the build regenerates `schema.d.ts`), FS-003 (session
  ownership), FS-007 (custom exam builder UI).

### FS batch 2 (2026-09-11, verified on board)
- **FS-002 auth frontend** — `api/auth.ts`, auth store extended
  (`login(username,password)` via `/api/auth/login`, rehydrate via `/api/auth/me`
  with legacy `/api/admin/check` fallback, legacy `loginAdmin` kept), LoginView
  id+password, `/dashboard` + `/exam/:sessionId` guarded roles
  `['admin','user']`; `openapi.json` + `gen:api` updated. Consolidated pass:
  lint/tsc clean, 235 vitest, build, 21 Playwright.
- **FS-003 session ownership** — `ExamSession.owner_username` + `assigned_by`;
  `web/api/session_ownership.py` per-user index; ownership populated at
  `/api/start`, `/api/presets/generate`, restore; invites record the assigner.
  **`var/session.json` retired** (user directive): `core/deployer.py` now uses
  the Redis session store exclusively, with an in-memory fallback in
  `core/redis_bus.py` when Redis is down, and a one-time legacy-file
  `.migrated` import. `get_timer`/`recorder` no longer read the file.
  `tests/test_session_store.py` (migration + ownership). Full suite 68 tests;
  only the 2 pre-existing host-only failures.
- **New task FS-003b** filed: true concurrent per-user sessions (replacing the
  single-active-session assumption) — depends FS-003 + FS-004.
- **Still not deployed to the host** — FS-001/002/003 all local; deploy before
  FE-044 (host-only auth endpoint tests + manual role flows belong there).

### Deploy (2026-09-11, after FS batch 2) + submit-route bug
- Deployed `web/api/`, `core/{redis_bus,deployer,models,recorder}.py`, and the
  rebuilt `web/dist` (FS-002 login UI) to `/root/cka-labs/`; `k8s-web.service`
  active; startup clean. Rollback: `/tmp/pre-fs-batch.tar.gz` on the host.
- **Bug found live: POST `/api/action/submit` returned 405.** The modularization
  moved its body to `web/api/services/submit.py` but `Agent A` never registered
  the route wrapper in `routes/exam.py`, so POST fell through to the GET-only SPA
  catch-all. Fixed by registering `@router.post("/api/action/submit")`.
  Guard added: `tests/test_route_inventory.py` asserts the full HTTP+WS route
  surface (parses route sources, Windows-safe) so a dropped route fails tests.
- **Login UX changed** with FS-002: `/login` is now username + password
  (bootstrap admin = `AUTH_ADMIN_USER`/`AUTH_ADMIN_PASSWORD`, fallback
  `admin`/`ADMIN_PASSWORD`). Legacy password-only admin login still exists via
  the store's `loginAdmin()` but the UI no longer uses it.

### FS batch 3 (2026-09-11, verified on board)
- **FS-004 admin assigns exam** — assignments are user-bound invitations
  (D-011): `core/redis_bus.py` gains `assigned_to`/`assigned_by` +
  `list/get_user/delete_assignment`; `web/api/routes/assignments.py`
  (`/api/admin/assignments` CRUD + `/api/assignments` for the current user);
  `api/assignments.ts` + `AdminAssignmentPanel.vue` mounted in `AdminView`.
- **FS-007 custom exam builder UI** — `PresetBuilder.vue` (count/difficulty/
  domains → `POST /api/presets/generate`, summary only, no question list);
  `api/presets.ts` gains `generatePreset`; mounted in `AdminView`.
  (`openapi.json` was not updated for these two; hand-typed clients used.)
- Consolidated: backend 75 tests (2 known host-only failures), frontend lint +
  tsc + 242 vitest + build + 21 Playwright. Board **38/47**.
- **Remaining FS:** FS-005 (user dashboard — unblocked), FS-008 (hide catalog
  from non-admins — unblocked), FS-003b (concurrent multi-user sessions).
- **Not deployed since the last host deploy** — FS-004/FS-007 backend + rebuilt
  frontend are local; deploy before FE-044 / testing.

### Deploy (2026-09-11, after FS batch 3)
- Deployed `web/api/` (incl. `routes/assignments.py` + registration),
  `core/redis_bus.py`, and the rebuilt `web/dist`; `k8s-web.service` active,
  startup clean. Rollback: `/tmp/pre-fs4.tar.gz` on the host.
- Probes (GET-only): `/api/assignments` → 401, `/api/admin/assignments` → 401,
  `/api/presets` → 200, `/` + `/admin` → 200.
- **Lesson:** never POST to a mutating endpoint (e.g. `/api/action/submit`) as a
  "probe" — an earlier probe submitted a live session. Use GET/health probes.

### FS batch 4 (2026-09-11, verified on board) — FS backlog complete except FS-003b
- **FS-005 user dashboard** — `DashboardView.vue` lists only the signed-in user's
  assignments (`GET /api/assignments`), Start navigates to `/?token=`; wired to
  `/dashboard`. No catalog access. `tests/unit/dashboard.test.ts` (8).
- **FS-008 hide catalog** — `GET /api/presets` + `POST /api/presets/select` +
  `POST /api/presets/generate` now `require_admin` (401 otherwise);
  `CandidateView` stops fetching the catalog and hides the preset picker for
  non-admins. `tests/test_preset_authz.py`. FE-042 candidate E2E specs updated
  (preset picker is admin-only).
- Consolidated: backend 81 tests (2 known host-only failures), frontend lint +
  tsc + 250 vitest + build + 21 Playwright. Board **40/47**.
- **Remaining:** FS-003b (concurrent multi-user sessions), FE-044, gates
  FE-V1..V5. FS-004/005/007/008 + this batch are **not deployed** yet.

### Deploy (2026-09-11, after FS batch 4)
- Deployed `web/api/` (FS-008 admin gates on `/api/presets*`) + rebuilt
  `web/dist` (FS-005 dashboard, FS-008 candidate catalog hidden); service active,
  startup clean. Rollback: `/tmp/pre-fs5.tar.gz` on the host.
- Probes (GET-only): `/api/presets` → 401 (FS-008 live), `/api/session` → 200,
  `/`, `/admin`, `/login` → 200.

### FS-003b + admin/candidate UX (2026-09-11, deployed; FS-003b in-review)
- **FS-003b concurrent sessions** (D-012): `active_sessions` set is the registry,
  `is_session_active` is membership-only; new `list_active_session_ids` +
  per-user `user:{u}:active_session` index; `web/api/session_resolver.py`
  resolves contextually (token → user → admin legacy pointer); `start_exam` /
  `presets/generate` replace only the caller's own session; background workers +
  admin/session lists iterate all live sessions; ws_terminal/desktop/events
  validate the explicit sid (no global pointer). `require_user` added;
  `/api/presets/generate` relaxed to any signed-in user (listing stays admin).
  `tests/test_multi_session.py`. Backend 86 tests (3 known host-only failures).
  **Live two-session concurrency still to be exercised (FE-044).**
- **Admin split** — config/invite/assign/builder moved to a new
  `/admin/settings` (`AdminSettingsView.vue`); `/admin` keeps sessions +
  infrastructure with a "Settings" button. E2E admin journey updated.
- **Candidate custom exam** — `PresetBuilder` now also renders on `/assignments`
  (hidden while a session is active); candidate start screen gained a
  "My assignments" button to `/assignments`.
- Deploy: `web/api` + `core/{redis_bus,deployer}.py` + `web/dist`; probes 200.
  Rollback: `/tmp/pre-fs3b.tar.gz` on the host.
- **Gotcha:** `tests/test_multi_session.py` must patch `bus.is_available = False`
  (an unreachable host makes redis-py retry and hang the whole suite).

### Users management UI + admin settings layout (2026-09-11, deployed)
- **`/admin/settings` layout:** Row 1 (2-col) Default preset + Create candidate
  invite; Row 2 (2-col) Server resources + Custom exam; then full-width
  **Assign exam** and new full-width **Users**.
- **Users panel** (`AdminUsersPanel.vue` + `api/users.ts`): add user (any
  password, role `user`/`admin`) + list + delete-with-confirm. Backend gained
  `DELETE /api/admin/users/{username}` (admin-only; 404 missing, 400 self /
  last-admin). Bootstrap admin is `admin` / `AUTH_ADMIN_PASSWORD`→
  `ADMIN_PASSWORD`→`admin123` (host: `admin`/`admin123`).
- Tests: `tests/test_admin_users.py`, `tests/unit/admin-users.test.ts`.
  Backend 91 tests, frontend 260 vitest + 21 Playwright.
- Deploy rollback: `/tmp/pre-users.tar.gz`.

### Channels / provisioning work (2026-09-11)
Plan (agreed): P1 conditional provisioning → P2 per-channel scrollback + render
fixes → P3 channel+actor tagging + replay tabs → P4 desktop terminal recording.
- **P1 (deployed):** `core/sandbox_orchestrator.py` `provision_plan(contexts)` —
  Incus/kubeadm only when `KUBEADM_CONTEXT` is in the session's contexts; k3d
  only for k3d contexts; desktop always; a preset with both provisions both.
  `provision_session(session_id, contexts=...)`; callers pass
  `session.target_contexts`; dead `ensure_k3d_cluster_running` removed.
  `tests/test_provision_plan.py` (7). Rollback `/tmp/pre-p1.tar.gz`.
- **P2 (deployed):** per-channel scrollback `terminal:buffer:{sid}:{channel}`
  (`append/get/clear/expire_terminal_buffer`), long TTL while active / 5 min for
  idle; **admin web terminal gets NO candidate scrollback and no buffer**
  (channel `admin-web`, fresh shell); `XTerm.vue` connects only when visible and
  `fit()` re-sends resize + repaints (fixes the duplicated prompt on first
  attach and the broken prompt on VNC↔terminal switches).
  Rollback `/tmp/pre-p2.tar.gz`.
- **Remaining: P3** (tag channel+actor on every frame/event, per-channel casts,
  replay dialog with `User | Admin` tabs + User Web/Desktop dropdown, shared
  clock), **P4** (record desktop terminal input+output via a fresh-pty wrapper;
  rebuild `cka-desktop:latest`). Admin desktop VNC stays view-only (already).
- **P3 (deployed):** recorder now writes **per-channel casts**
  `{sid}.{channel}.cast` (`user-web`/`admin-web`/`user-desktop`; legacy
  `{sid}.cast` ≡ user-web) via `record_output/input/resize(..., channel=)` and
  `log_event(..., channel=)`; events carry `channel`; `get_cast_path(sid,
  channel)`, `get_recording` returns `channels:[{id,has_cast,cast_size_bytes}]`;
  `/api/recordings/{sid}/cast?channel=`; desktop-agent events log as
  `user-desktop`/`user`. Replay UI: `RecordingsModal` gets **User | Admin tabs**
  (User has a Web/Desktop dropdown), `ReplayPlayer` takes `sessionId`+`channel`
  and preserves the playhead across channel switches. Tests:
  `tests/test_channel_recording.py`, `tests/unit/{recordings-api,replay-player,
  recordings-modal}.test.ts`. Rollback `/tmp/pre-p3.tar.gz`.
- **Remaining: P4** — record the desktop terminal's input+output via a fresh-pty
  wrapper + rebuild `cka-desktop:latest`.

### P4 + replay/notify follow-ups (2026-09-11, deployed)
- **P4 desktop terminal recording:** `docker/desktop/desk-terminal-record.py` runs
  the in-desktop shell under a local pty and publishes input+output to
  `events:{sid}` as `user-desktop`/`user`; `entrypoint.sh` launches
  `xfce4-terminal -e desk-terminal-record.py`; the recorder subscriber turns
  `DESKTOP_TERMINAL_OUTPUT` → cast frames and `DESKTOP_TERMINAL_INPUT` →
  `record_input(channel=user-desktop)`; retired the `xinput` key sniffer
  (`desk-agent.py`). Image rebuilt (`cka-desktop:pre-p4` rollback).
- **Replay UI rework:** `User` is now a dropdown (Web/Desktop) beside an `Admin`
  tab, aligned with the Events/Tasks row; events are filtered by channel (legacy
  no-channel = user-web); "Download .cast" buttons removed. (Tasks remain
  session-global — no channel field.)
- **Admin → candidate notification:** `POST /api/admin/sessions/{id}/notify`
  publishes `admin_notification` to `notify:{sid}` (desk-agent shows an
  `xmessage` popup) + `session:{sid}`; Observe overlay gets a **Notify** button +
  modal. `core/redis_bus.publish_notification`. Image rebuilt
  (`cka-desktop:pre-notify` rollback).
- Rollback: `/tmp/pre-notify.tar.gz` (web/api, redis_bus, dist, desk-agent).
- **Note:** running desktops keep the old image; new sessions pick up the new
  one. P4/notify not yet exercised live.
- **Notify gotcha (resolved):** desktop-image changes only apply to *newly
  created* desktop containers. A live session on the old image showed nothing.
  Recreate with `desktop_mgr.stop_desktop(sid); start_desktop(sid)` (or start a
  new session). Verified end-to-end: `pubsub numsub notify:{sid}` = 1,
  publish receiver = 1, `xmessage` popup process present in the container.

### Full redeploy (2026-09-11)
- Redeployed the whole local state: `web/api/`, `core/` (all), rebuilt
  `web/dist`. `py_compile` + `import web.server` clean; `k8s-web.service` active;
  `/`, `/assignments`, `/admin`, `/admin/settings`, `/login`, `/api/session` → 200.
- Desktop image already current (P4 + notify listener); no rebuild this pass.
- Rollback: `/tmp/pre-final.tar.gz` (web/api, core, web/dist, traefik, desktop).

### Post-batch-4 fixes (2026-09-11, user-reported)
- **`/dashboard` collided with Traefik.** Traefik owns `PathPrefix('/dashboard')`
  (its own secured dashboard), so the SPA route was shadowed. Renamed the user
  dashboard to **`/assignments`** (D-011 amendment).
- **"Unauthorized" on the dashboard** — a legacy `admin_token` cookie satisfied
  the route guard but `/api/assignments` needs a real user auth session; the view
  now redirects to `/login?redirect=/assignments` when unauthenticated.
- **`/` is not a public landing page.** On mount it resolves the auth session
  and any resumable session; if there is no sign-in, no `?token=` invitation and
  no live/persisted session it **redirects to `/login?redirect=/`**. Invitation
  links and signed-in users continue normally (candidates can resume a running
  exam without logging in via the persisted `cka:candidate-token`).
- **The candidate route no longer renders a preset picker at all** (removed the
  "Choose preset" button + `PresetModal`); presets are administered from
  `/admin`. `PresetModal.vue` is now unused (left in place). Note: a persisted
  `admin_token`/`cka_auth_token` cookie makes `/` resolve as an authenticated
  admin — that path shows Start but no catalog controls.
- **Admin "Start now"** added to `AdminInviteForm` (user decision): after
  generating an invite, an admin can launch that preset/assignment immediately
  (`POST /api/start {candidate_token}` then route to `/?token=…`). This replaces
  the removed candidate-route picker for admins.
- Verified: frontend lint + tsc + 250 vitest + build + 21 Playwright (E2E
  fixtures updated to authenticate the candidate).
