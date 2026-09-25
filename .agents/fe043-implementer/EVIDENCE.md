# EVIDENCE — FE-043

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-fe043 (2026-09-11)

- Deliverable: docs aligned with the post-FE-040 frontend (Vite build-on-deploy,
  Node requirement, current SPA architecture, no dead links).
- Files touched:
  - `README.md` — new "Frontend Build (Vue 3 SPA)" subsection (build-on-deploy,
    Node.js >= 20.19 + npm, `web/dist` git-ignored, 503 until built, dev workflow);
    fixed "Documentation Links" (removed deleted `HANDOVER.md`/`STATUS.md` and the
    `file:///home/amazinrahul/...` absolute paths; relative links to
    `PLATFORM_SETUP.md`, `PRD.md`, `CONCURRENT_MULTI_NODE_ARCHITECTURE.md`,
    `web/frontend/README.md`).
  - `PLATFORM_SETUP.md` — added an IMPORTANT "Frontend build prerequisite" callout
    (Node.js >= 20.19 + npm; `setup-platform.sh` does not install Node) and expanded
    the systemd `ExecStartPre` section into a "Frontend build (Vue 3 + Vite)"
    subsection (build helper behaviour, invoked by `start-web.sh` + systemd,
    `web/dist` git-ignored/D-005, 503 until built, dev command).
  - `.agents/frontend-migration/HANDOVER.md` — refreshed the status snapshot
    (FE-033/FE-040 verified; remaining FE-041..044 + gates + FS backlog) and added a
    "Frontend architecture (Vue 3 + Vite SPA)" subsection. Also corrected the stale
    `web/static` "do not touch" note and the stale §9 next-action list.
  - `web/frontend/README.md` — rewrote the "Structure" section (no `src/islands/`;
    islands live in `components/workspace/`), added `components/{admin,candidate,layout,ui}/`,
    `composables/`, `stores/`, `api/`, `assets/styles/`, `tests/{unit,e2e}`.

- Commands run + output:
  ```
  $ git grep -n 'STATUS.md\|HANDOVER.md' -- README.md
  (no output; exit 1 → no matches)

  $ @('PLATFORM_SETUP.md','PRD.md','CONCURRENT_MULTI_NODE_ARCHITECTURE.md','web/frontend/README.md') | %{ "$_ exists=$(Test-Path $_)" }
  PLATFORM_SETUP.md                             exists=True
  PRD.md                                        exists=True
  CONCURRENT_MULTI_NODE_ARCHITECTURE.md         exists=True
  web/frontend/README.md                         exists=True

  $ git diff --stat -- <4 files>
   .agents/frontend-migration/HANDOVER.md | 60 +++++++++++++++++++++++-----------
   PLATFORM_SETUP.md                      | 37 +++++++++++++++++----
   README.md                              | 29 +++++++++++++---
   web/frontend/README.md                 | 18 +++++++---
   4 files changed, 111 insertions(+), 33 deletions(-)
  ```
- Spot-checked claims against the repo:
  - `tools/build-frontend.sh` — `npm ci && npm run build`, else `bun install && bun run build`;
    warns + exits 0 if neither present; errors if `web/dist/index.html` missing.
  - `web/frontend/package.json` — `"engines": { "node": ">=20.19.0" }`; scripts `dev`,
    `build` (gen-api + `vue-tsc --noEmit` + `vite build`), `typecheck`, `lint`, `test`,
    `test:e2e`, `gen:api` all present as documented.
  - `web/server.py` — `DIST_DIR = web/dist`, `SPA_INDEX = web/dist/index.html`;
    `/admin` and the SPA fallback return **503** (`Frontend build missing; run
    tools/build-frontend.sh`) when the build is absent; `web/static` is gone.
  - `tools/start-web.sh` — invokes `tools/build-frontend.sh` before uvicorn.
- Screenshots: n/a
- Test cases executed (see TESTPLAN.md): T2 PASS; T1 DEFERRED (no clean Linux host
  available in this sandbox; host steps recorded in TESTPLAN.md).
- Self-check against acceptance criteria:
  1. README reflects the Vite build step — PASS (`### Frontend Build (Vue 3 SPA)`).
  2. HANDOVER documents frontend architecture — PASS (new architecture subsection +
     refreshed status snapshot).
  3. PLATFORM_SETUP lists the Node requirement — PASS (prerequisite callout +
     "Frontend build" subsection both state Node.js >= 20.19 + npm).

## Verifier — <different agent> (<UTC>)
- Clean checkout / environment: <describe>
- Re-ran acceptance commands:
  ```
  <commands and observed output>
  ```
- Test cases re-run independently (see TESTPLAN.md): <T1 PASS/FAIL, T2 PASS/FAIL>
- Criterion-by-criterion result:
  1. <criterion> — PASS/FAIL — <evidence>
- Regression checks (WS, clipboard, timer, a11y, contrast): <result>
- Verdict: `verified` | `rejected` — <reasons if rejected>
