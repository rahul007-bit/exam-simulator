# TESTPLAN — FE-003

Per-task test plan. The **implementer** fills in the executed results; the
**independent verifier** re-runs and records their own results (do not copy the
implementer's numbers).

Test cases are defined canonically in `tasks.json` (task `FE-003` → `tests`).
Mirror them here, then add any edge cases discovered during work.

## Test cases

| ID | Type | Run | Expected | Implementer result | Verifier result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| T1 | integration | `curl -s localhost:3000/` | SPA index returned | **DEFERRED (host-only)** — no backend/FastAPI on this host. Static equivalent: built `web/dist/index.html` contains `<div id="app">` + `/assets/index-*.js`; `/` handled by catch-all when `DIST_DIR.is_dir()`. | **DEFERRED (host-only)** — verifier-2 confirms `import pty` fails on Windows (`No module named 'termios'`). Local: actual `spa_fallback("")` body returns built index with `id="app"`; `get_admin_page` returns SPA index. |
| T2 | integration | `curl -s -o /dev/null -w '%{http_code}' localhost:3000/api/session` | `200` | **DEFERRED (host-only)**. Static equivalent: `/api/session` handler unchanged and registered at L334, before the catch-all (audited). | **DEFERRED (host-only)**. Local: route-parity 50/50; `/api/session` at L334 registered before catch-all L2369. Live 200 → host. |
| T3 | integration | `python scripts/verify_platform_api.py` | pass | **DEFERRED (host-only)** — requires Linux backend, Redis, docker/incus/k3d. | **DEFERRED (host-only)** — verifier-2 can only lint the script; needs live :3000 + Redis + docker/incus/k3d. See host commands below. |

### Local equivalents (executed here, Windows + WSL bash)

| ID | Type | Run | Expected | Implementer result |
| :--- | :--- | :--- | :--- | :--- |
| L1 | audit | `python -m py_compile web/server.py` | syntax OK | **PASS** — exit 0 |
| L2 | audit | `python .agents/FE-003-implementer-1/route_order_audit.py` | catch-all last; `/api`,`/ws`,`/novnc` before it | **PASS** — exit 0, 56 registrations checked |
| L3 | integration | `bun run build` (from `web/frontend`) | emits `web/dist/index.html` + `/assets/*` | **PASS** — `web/dist/index.html` 1.24 kB, `/assets/index-DBN6VICQ.js` |
| L4 | integration | `bash tools/build-frontend.sh` (no npm/bun) | guarded no-op, exit 0 | **PASS** — warning + exit 0 |
| L5 | unit | fake npm/bun on PATH + edge cases (fail / missing index / no scaffold) | correct branch + exit codes | **PASS** — branches A–E as designed |
| L6 | audit | `bash -x tools/start-web.sh` (fake npm) | build helper runs before uvicorn | **PASS** — trace shows `tools/build-frontend.sh` then `exec ... uvicorn` |

## Edge cases / additions
- `web/dist` absent → server takes the `else` branch and mounts legacy
  `web/static` at `/` (original behaviour preserved; audited as `[else@2361]`).
- Unknown `/api/...` or `/ws/...` path → catch-all returns 404, never `index.html`.
- Path traversal (`/../...`) into `web/dist` → `is_relative_to` guard prevents
  serving files outside the build dir.
- `web/dist` present but `assets/` missing → `/assets` mount skipped (guarded),
  catch-all still serves `index.html`.
- Build failure on deploy → `build-frontend.sh` exits non-zero so deploy is loud;
  no-tooling host exits 0 and keeps the legacy UI.

## Environment
- Commit / build: branch `feature/frontend-vue-migration`, HEAD `e0fb4a3`
  (deliverable is uncommitted working-tree work, per instructions not to commit).
- Host: Windows 11 workstation; Bun 1.4.2; no npm/node/rg; Python 3.12.4; WSL bash 5.3.9.
- Backend: **not runnable here** (Linux-only `pty`/`fcntl`/`termios`; FastAPI/uvicorn absent).
- Browser(s): n/a.

## Verdict
- Implementer: **PASS (local equivalents L1–L6); T1–T3 DEFERRED host-only** — 2026-09-10T06:21:12Z
- Verifier: **PASS (local equivalents V1–V8); T1–T3 DEFERRED host-only** — verifier-2, 2026-09-10T06:26:14Z

### Verifier local equivalents (verifier-2, re-derived independently)

| ID | Type | Run | Expected | Verifier result |
| :--- | :--- | :--- | :--- | :--- |
| V1 | audit | `python -m py_compile web/server.py` | syntax OK | **PASS** — exit 0 |
| V2 | audit | `python scripts/agents_board.py --check` | validation OK | **PASS** — `validation OK (44 tasks)`, exit 0 |
| V3 | audit | verifier-2 own `ast` route audit (temp script) | catch-all last; all /api,/ws,/novnc before it | **PASS** — 1 catch-all (L2369); 40 `/api`, 6 `/ws`, `/novnc` mount L2353; root mount only in `else` L2396 |
| V4 | unit | execute **actual** `spa_fallback`/`get_admin_page` bodies (AST-extracted) with stubs | api/ws/novnc → 404; traversal → no leak; app routes → index | **PASS** — all cases as expected |
| V5 | audit | route parity vs `git show HEAD:web/server.py` | no /api,/ws route removed/renamed | **PASS** — 50/50, zero removed/added |
| V6 | integration | `bun run build` (`npm run build` equivalent) | emits `web/dist/index.html` + `/assets/*` | **PASS** — 41 modules, index-DBN6VICQ.js, 425ms |
| V7 | audit | `git ls-files web/dist` + `git check-ignore` + `git status --ignored` | not committed, ignored | **PASS** — empty; `.gitignore:11:web/dist/`; `!! web/dist/` |
| V8 | integration | `bash tools/build-frontend.sh` branch matrix A–F + `bash -n` | guarded no-op / correct exit codes | **PASS** — A,E,F exit 0; B exit 0; C,D exit 1; syntax exit 0 |

### Host-only commands for the platform-host verifier (run exactly)

```bash
# Preconditions: platform host, Node >= 20.19 + npm (or bun), Redis, docker, incus,
# k3d, and the backend stack installed. Branch: feature/frontend-vue-migration.
cd /root/cka-labs

# T1 — SPA served at / (expect built index -> <div id="app">, /assets refs)
curl -s http://localhost:3000/ | head
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/admin      # expect 200

# T2 — existing REST route still 200
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/api/session  # expect 200

# Confirm catch-all does NOT serve index for API/WS/novnc prefixes
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/api/does_not_exist    # expect 404
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/novnc/does_not_exist  # expect 404

# T3 — full API platform verification (admin + candidate + teardown regression)
python scripts/verify_platform_api.py

# Build-on-deploy integration
bash tools/build-frontend.sh && ls -l web/dist/index.html
systemctl show -p ExecStartPre cka-web    # or: cat /etc/systemd/system/cka-web.service
```

> T1/T2/T3 are **DEFERRED** locally (Windows host cannot import `web/server.py`;
> Linux-only `pty`/`fcntl`/`termios` + Redis/docker/incus/k3d). They must be run
> on the platform host before the M1 gate (FE-V1).

## Host verification — platform host `10.8.0.15` (orchestrator, 2026-09-10)

Method: an isolated instance of the FE-003 server module (`web/server_fe003.py`, i.e.
the modified `web/server.py`) was run on `127.0.0.1:3001` with the built `web/dist`
copied to the host. The live `k8s-web.service` on `:3000` was left untouched; the temp
instance was stopped and its host artifacts removed afterward.

| ID | Run | Expected | Result |
| :--- | :--- | :--- | :--- |
| T1 | `curl /`, `/admin`, `/login`, `/dashboard` | SPA index 200 with `#app` + `/assets` refs; SPA fallback for app routes | **PASS** |
| T2 | `curl /api/session`, `/api/does_not_exist`, `/novnc/does_not_exist` | 200 JSON; 404; 404 | **PASS** |
| assets | `curl /assets/<hashed file>` | 200 | **PASS** |

Host probe result: **11 passed, 0 failed**. See EVIDENCE.md "Host execution" section.

- **T3 `verify_platform_api.py` NOT run**: it provisions an Incus fleet (`wait_fleet`
  up to 420s) and mutates live platform state. It is reserved for a dedicated
  platform-test run / the M1 gate (FE-V1), not a casual verification step.

### Host deploy prerequisites uncovered (action required before M5 cutover)
- The platform host has **Node v22.22.1 but no `npm`** (Ubuntu ships npm as a separate
  package) and **no `bun`**, so `tools/build-frontend.sh` currently no-ops there and the
  server serves the legacy UI. Fix: install npm, or extend the helper to use `corepack`
  / `npx` (corepack 0.24.0 is present and can run npm).
- `web/frontend/package-lock.json` is absent, so the helper's preferred `npm ci` cannot
  run. Generate and commit a lockfile (or use `npm install`) before cutover.
