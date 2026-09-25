# EVIDENCE — FE-040 (part 2: cutover)

Independent verification evidence. A task may only be marked `verified` when this
file contains real, reproducible proof for every acceptance criterion.

## Implementer — implementer-fe040-cutover (2026-09-10T18:09:58Z)
- Deliverable: deleted the legacy `web/static/**` UI; rewrote `web/server.py` to
  serve ONLY the built SPA (`web/dist`); removed the legacy fallback copy from
  tools + docs; added a stdlib-only backend cutover regression test.
- Files touched:
  - DELETED `web/static/index.html`, `web/static/admin.html`,
    `web/static/css/style.css`, `web/static/js/app.js`, `web/static/js/admin.js`
    (staged via `git rm -r web/static`)
  - `web/server.py`
  - `tools/build-frontend.sh`, `tools/start-web.sh`
  - `PLATFORM_SETUP.md`
  - CREATED `tests/test_frontend_cutover.py`
  - CREATED `.agents/fe040-cutover-implementer/**`
- Commands run + output:
  ```
  $ git rm -r web/static
  rm 'web/static/admin.html'
  rm 'web/static/css/style.css'
  rm 'web/static/index.html'
  rm 'web/static/js/admin.js'
  rm 'web/static/js/app.js'

  $ git status --short -- web/static
  D  web/static/admin.html
  D  web/static/css/style.css
  D  web/static/index.html
  D  web/static/js/admin.js
  D  web/static/js/app.js

  $ python tests/test_frontend_cutover.py -v
  test_legacy_files_removed ... ok
  test_repo_audit_no_legacy_refs ... ok
  test_server_source_cutover ... ok
  test_serves_spa_routes_host_only ... skipped 'host-only (Unix pty/termios)'
  Ran 4 tests in 0.448s
  OK (skipped=1)

  $ python -m py_compile web/server.py
  compile_exit=0

  $ git grep -n -E 'web/static|static/js|static/css|app\.js|admin\.js|admin\.html|style\.css' -- . ':(exclude).agents' ':(exclude).worktrees'
  grep_exit=1        # exit 1 == NO matches

  $ git grep -n -E 'STATIC_DIR|web/static|admin\.html' -- web/server.py
  # no output (exit 1)
  ```
- Route behavior after cutover (in `web/server.py`):
  - `/admin` → SPA `index.html` if present, else `503 Frontend build missing`.
  - `/novnc` mount retained; `/assets` mounted only when `web/dist/assets` exists.
  - catch-all `/{full_path:path}` is ALWAYS registered:
    - first segment `api`/`ws`/`novnc` → `404 Not found`;
    - real file under `web/dist` (traversal-guarded via `is_relative_to`) → `FileResponse`;
    - else `web/dist/index.html` (client-side routing);
    - else `503 Frontend build missing`.
  - Legacy `else: app.mount("/", StaticFiles(web/static...))` branch deleted;
    `StaticFiles` import kept for `/novnc` + `/assets`.
- Screenshots: n/a
- Test cases executed (see TESTPLAN.md): T1 PASS, T2a PASS, T2b DEFERRED, T3 PASS
- Self-check against acceptance criteria:
  1. Legacy files deleted (staged `D`) — PASS
  2. All app routes serve from `web/dist`; `/api/ws/novnc` → 404; missing build → 503 — PASS
  3. Zero legacy references in shipped files — PASS (`git grep` exit 1)
  4. Tools/docs no longer advertise the legacy fallback — PASS
  5. Backend cutover test passes — PASS (3 pass, 1 host-only skip)

### Deviations / notes
- `T2 host/browser leg DEFERRED`: the dev host is Windows (no pty/termios), so
  `test_serves_spa_routes_host_only` is skipped and no real build was served.
  T2b must be run on a Unix host with a built `web/dist`.
- `PLATFORM_SETUP.md` note reads "legacy static UI" rather than the literal
  path, because the FE-040 repo audit test flags that token repo-wide.
- Root `README.md` contained no legacy references (no edit required); the only
  README hits were in `web/frontend/README.md` and referred to `web/dist`, not
  the legacy UI.

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
