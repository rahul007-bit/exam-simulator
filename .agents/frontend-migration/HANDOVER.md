# HANDOVER — Frontend Migration (continue this session)

Written: 2026-09-10. Branch: **`feature/frontend-vue-migration`** (based on `feature/phase-3-arch`).
Everything is **uncommitted in the working tree** (the user has not asked for commits — do not commit unless asked).

## 1. Mission

Migrate the legacy vanilla-JS frontend to **Vue 3 + TypeScript + Vite** with a professional
slate+indigo design system (dark + light), preserving strict behavioral parity. Full plan:
`.agents/frontend-migration/PLAN.md`; decisions: `decisions.md`.

## 2. Status snapshot

- Board: **29 verified, 17 todo** (46 tasks). `python scripts/agents_board.py --check` is green.
- Verified: `FE-000..005, 010..014, 020..036` (incl. `FE-033` admin create invite and `FE-040`
  legacy removal + static cutover).
- Remaining todo: `FE-041..044`, gates `FE-V1..V5`, backlog `FS-001..008`.

### Remaining tasks
| ID | Depends | Title |
|---|---|---|
| FE-041 | FE-040 | Self-host fonts/deps (offline) |
| FE-042 | FE-040 | Playwright E2E + axe |
| FE-043 | FE-040 | Update docs |
| FE-044 | FE-042 | Full regression vs real backend |
| FE-V1..V4 | phase tasks | Milestone independent-verification gates |
| FE-V5 | FE-040..044 | Victory audit |

**Immediate next:** **FE-040** (legacy removal + static cutover) is **done/verified**, so
**FE-041** (self-host assets), **FE-042** (E2E + axe) and **FE-043** (docs) are running in
parallel on disjoint file sets. After they land, run **FE-044** (full regression vs the real
backend), then the gates **FE-V1..V5**.

## 3. Where everything lives

- Program workspace / rules / board: `.agents/frontend-migration/`
  - `PROTOCOL.md` (§9 = parallel-batch + verification rules — read this first)
  - `PLAN.md`, `decisions.md` (D-001..D-009), `ORIGINAL_REQUEST.md`
  - `tasks.json` (canonical) + `BOARD.md` (generated), `templates/`
  - `scripts/agents_board.py` (CLI: `--check --claim ID AGENT --force REASON --status --set-evidence --verify --unclaim --reject`)
- Frontend app: `web/frontend/` (Vue 3 + TS + Vite, **Tailwind v4** via `@tailwindcss/vite`, `@headlessui/vue`,
  Pinia, vue-router, `@tanstack/vue-table`, xterm, marked+DOMPurify+highlight.js, axe-core).
- Backend: `web/server.py` serves the built SPA (`web/dist`) with a client-side-routing fallback and
  owns `/admin`; since the FE-040 cutover there is **no** legacy `web/static` UI — the built SPA is
  the only UI and the server returns **503** until `web/dist` exists. Build helper
  `tools/build-frontend.sh` (called by `tools/start-web.sh` and the systemd `ExecStartPre`).

### Frontend architecture (Vue 3 + Vite SPA)

- **Stack:** Vue 3 + TypeScript + Vite, **Tailwind v4** (`@tailwindcss/vite`), Headless UI, Pinia,
  vue-router, TanStack Table, xterm (+ fit addon), noVNC (hosted at `/novnc`), marked + DOMPurify +
  highlight.js; axe-core + Playwright/Vitest for tests.
- **Source layout (`web/frontend/src/`):**
  - `views/` — route views (`CandidateView`, `AdminView`, `LoginView`, `DevUiView`, `PlaceholderView`)
  - `components/layout/` — `AppShell`, `AppHeader`, `OverflowMenu`, `WorkspaceSplit`
  - `components/ui/` — design-system primitives (`Button`, `Modal`, `DataTable`, `Select`, ...)
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
bun install                 # Bun 1.4.2 is available; npm may also be present
bunx vue-tsc --noEmit       # typecheck (.vue included)
bun run lint                # eslint
bun run test                # vitest (currently ~surfaced 176+ tests, all green at last full run)
bun run build               # gen:api (offline snapshot) + vue-tsc + vite -> web/dist
npx playwright test         # chromium; config webServer = `npm run dev`
```
- `bun run build` regenerates the git-ignored `src/api/schema.d.ts` from `web/frontend/openapi.json`
  (a curated snapshot; FE-004). No backend needed to build.
- Vitest prints `localStorage is not available...` warnings under Node — benign.

## 6. Environment / host

- Dev happens on this Windows workstation; **Bun 1.4.2** is the reliable runtime. npm availability has
  fluctuated (it was present as 11.19.1 at one point). Use `bun run ...`; `npx playwright test` works.
- Linux platform host: **`root@10.8.0.15`** (`exam-standardpc`), FastAPI live on `:3000`, deployed at
  `/root/cka-labs` (**not a git repo** — older code; do not assume it matches the branch).
  - Host has Node 22 but **npm is not on the default PATH** (Ubuntu split package); `corepack` exists.
    If you build on the host, use `corepack npm` or install npm.
  - The VPN path had an MTU black-hole (small responses OK, large/`scp` stalled). The user fixed the
    client (OpenVPN DCO MTU). If bulk HTTP/scp stalls again, it's MTU — don't chase app bugs.
  - Host-only verification pattern: copy the modified `web/server.py` as `web/server_fe003.py`, run an
    isolated `uvicorn` on `127.0.0.1:3001` with `web/dist`, probe via a script run **on the host**
    (loopback is unaffected by the VPN MTU). `python scripts/verify_platform_api.py` runs on a host and
    provisions an Incus fleet — run it only when intended (it was passed once: 44/0).

## 7. Key architecture / gotchas

- **Design system:** tokens in `src/assets/styles/tokens.css` (do not change values; tests assert them);
  Tailwind `@theme inline` maps them in `base.css`. No raw hex in `src/components`/`src/views`
  (`hex-audit` test), no glow/emoji (`decor-audit` test).
- **Shell:** `App.vue` suppresses the global topbar on the candidate route; `ThemeToggle` lives inside
  the candidate `AppHeader`. `CandidateView.vue` owns the AppShell + `WorkspaceSplit` + `WorkspaceTabs`
  (noVNC/XTerm), with `ClipboardBridge` and `FullscreenGuard` mounted.
- **Split pane:** drag the gutter fully left to collapse the left pane; a chevron button toggles it;
  the collapsed state persists (`cka:workspace:split:collapsed`).
- **Admin:** auth guard (FE-030) + `AdminView` (sessions table, config/resource forms, infrastructure
  table, observe overlay). Mutations are **non-blocking / per-row** (FE-036) — keep that behavior.
- **Vite dev proxy** logs `ECONNREFUSED` for `/api/*` because no backend is local — **benign** (the
  user accepted this).
- **Board CLI** requires evidence before `in-review`/`verified`; `--claim` enforces the dep gate.
- **Pre-existing, not ours — do not touch/delete:** modified `core/deployer.py`, `core/k3d_manager.py`,
  `docker/desktop/entrypoint.sh`, and the many untracked `scratch/*` files. The legacy `web/static`
  UI (`index/admin.html`, `js/app.js`) was **deleted in FE-040** — do not restore it. (A past subagent
  deleted `ansible/*.cfg|ini`; it was restored — keep an eye out and use `git restore` if it recurs.)

## 8. Known integration gaps / TODOs

- Question navigator (FE-024 `QuestionDrawer`) **is** wired inside `AppShell`: the AppHeader progress
  button emits `open-questions` → drawer opens; task selection forwards via AppShell `select-task`
  (handled by `CandidateView.onSelectTask`). No action needed.
- Overflow actions still TODO in `CandidateView.onAction`: `reload`, `new-tab` (→ FE-026 frame).
- FE-029 recordings is wired via the overflow **Recordings** action.
- FE-033 not started → blocks FE-040 and FE-V4.
- Browser/e2e legs were broadly **DEFERRED** during the testing-paused batches; the milestone gates
  (FE-V1..V5) are where they must be run (Playwright + axe).

## 9. Suggested next actions

1. `python scripts/agents_board.py --check`
2. **FE-033 (admin create invite)** and **FE-040 (legacy removal + static cutover)** are **done/verified**.
3. Batch **FE-041 (self-host assets)**, **FE-042 (E2E+axe)** and **FE-043 (docs)** in parallel; then
   **FE-044** (full regression vs real backend).
4. Run **FE-V1..V5** gates (independent verification) and close out.

## 10. Session fixes (2026-09-10, uncommitted — parity gaps not yet on the board)

These were raised by the user while exercising the SPA against the live platform host. They are
**untracked parity gaps** (the board's acceptance criteria were narrower than the legacy behaviour);
consider filing them as `FE-0xx`/`FS` tasks so the gates re-cover them. All frontend checks were run
after each change: `bunx vue-tsc --noEmit`, `bun run lint`, `bun run test` (176/176), `bun run build`
(`web/dist` rebuilt for the `:4173` preview).

### Frontend (`web/frontend`, untracked)
- **Admin page couldn't scroll** — `App.vue` locked every route to `height:100vh; overflow:hidden`.
  Made the fixed shell conditional (`app-shell--fixed`, candidate route only); admin/login now scroll.
  Also made `showTopbar` null-safe (`route?.name`) — the unit smoke test mounts without a router.
- **Preset modal** — removed the inherited `ul` left padding (symmetric insets) and styled the list
  scrollbar (`PresetModal.vue`).
- **Candidate header** — a dedicated `warning` Button variant (added to `ui/types.ts` + `Button.vue`);
  Flag now uses it instead of danger; the progress/task-list button is a real button (`secondary`);
  the session ID is shown beside it as a click-to-copy chip (emits `copy-session-id` → `CandidateView`).
- **Clipboard (FE-027 parity)** — `ClipboardBridge` connected once to `/ws/session/active` before the
  store hydrated (`main.ts` hydrates after mount) and never rebound. It now watches `[sessionId,
  active]` and reconnects. Also `TaskPane` re-emits the markdown code-copy event and `CandidateView`
  mirrors it into the desktop via `sendToVnc` (legacy `copyCode`/`copyInlineCode` → `syncTextToVnc`),
  fixing host → VNC.
- **Observe overlay (FE-035 parity)** — added the task-instructions pane (badges + sanitized markdown),
  the "All tasks in exam" list, a **Review & replay** button, and a resizable left pane reusing
  `WorkspaceSplit` (`cka:observe:split`). Lowered the overlay from `z-[1100]` to `z-[900]` so global
  dialogs/toasts (z-1000) are above it (its own confirm dialogs and the review modal were hidden).
- **Replay UI (modernised, not a legacy replica)** — wide `xl` modal, timeline left (Events/Tasks,
  click-to-seek) and large terminal right, transport with `-10s`/`+10s`/Restart/Speed (`ReplayPlayer.vue`,
  `RecordingsModal.vue`). `showList`/`showEvents`/`initialSessionId` props scope the admin/observe
  review to one session; added a visible **Close**. Distinct Badge colour per event type. Tab headers
  aligned; duplicate exam name removed.
- **Crash fix (important)** — `Select.vue` (Headless UI `Listbox`) threw `Passing props on "template"!`
  when any extra attr (e.g. `aria-label` from the replay speed picker) was passed, which killed the
  whole Vue render (blank replay + frozen buttons). Fixed with `inheritAttrs:false` + `v-bind="$attrs"`
  on the `ListboxButton`.
- **Manage session dialog** — actions are a 2-column grid (not a vertical stack) and gained **Review &
  replay**; `AdminView` opens the replay scoped to that row's session.
- **Candidate start feedback** — the start screen shows a loading button + live status line while the
  backend provisions the environment.
- **Global scrollbars** — slim token-coloured scrollbars added in `base.css`.

### Backend (tracked)
- **`core/recorder.py`** — `_find_places_db` now also searches Snap/Flatpak Firefox profiles, honours
  `FIREFOX_PROFILE_DIR`, prefers the most-recently-used profile, and (with `RECORDER_DEBUG=1`) warns
  once when no profile is found. Additive/backward-compatible; `py_compile` clean. Kept as a fallback.
- **`docker/desktop/desk-agent.py`** — the browser runs **inside the desktop container**, so the
  host-side poller can never see its Firefox profile. Added `start_browser_history_poller` in the
  sidecar (reads the container-local `places.sqlite`, publishes `BROWSER_NAVIGATE`/`BROWSER_SEARCH` to
  `events:{session_id}`; the recorder's existing Redis subscriber logs them). Also **suppressed
  `WINDOW_FOCUS` for browser windows** so browser activity has a single source (option 2). `py_compile`
  clean.

**Deploy required for the backend fixes:** rebuild/redeploy the desktop container image (desk-agent is
baked in) and, if the host fallback is wanted, copy `core/recorder.py` to `root@10.8.0.15:/root/cka-labs/`
and restart the web service. No frontend change is needed for these.

**Still open / not addressed:** a live timer in the observe overlay; Chromium-based browsers are not
tracked (Firefox only).
