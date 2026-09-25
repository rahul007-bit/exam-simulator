# FE-040 — Independent verification (verifier-fe040)

Status: **PASS** (T2 host-only leg DEFERRED)
Verifier: `verifier-fe040` (independent of `implementer-fe040-purge` / `implementer-fe040-cutover`)
Date: 2026-09-11

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| Legacy files deleted | PASS | `web/static/` gone; staged `D web/static/{index.html,admin.html,css/style.css,js/app.js,js/admin.js}`; no reintroduction (`glob **/app.js`, `**/admin.js` → none). |
| All routes serve from `web/dist` | PASS | `/admin` → `SPA_INDEX` or 503; catch-all `/{full_path:path}` always registered; real dist files via traversal-guarded `is_relative_to`; SPA index fallback; `api|ws|novnc` → 404; only mounts `/novnc` and `/assets`. |
| No 404s or dead references | PASS | `git grep -n -E 'web/static\|static/js\|static/css\|app\.js\|admin\.js\|admin\.html\|style\.css' -- . ':(exclude).agents' ':(exclude).worktrees'` → exit 1, zero hits. |

## Tests

- T1 (audit): PASS — repo-wide shipped-tree grep returns zero; frontend tree purged (comments/tests included).
- T2 (integration, navigate `/` and `/admin`): **DEFERRED** — Windows dev box cannot import `web/server.py` (`pty`/`termios`/`fcntl` unavailable). Represented locally by `test_server_source_cutover` + direct source inspection. Must run on the Linux host / FE-V5 gate with `web/dist` built (`web/dist/index.html` contains `<div id="app"></div>`).

## Commands

- `python tests/test_frontend_cutover.py -v` → `Ran 4 tests ... OK (skipped=1)` (3 pass, host-only skipped).
- `web/frontend`: `bun run lint` → pass; `bunx vue-tsc --noEmit` → pass; `bun run test` → **19 files / 209 tests passed**.
- `python -m py_compile web/server.py` → exit 0.
- `git grep` legacy-token audit (shipped tree) → zero.

## Notes / concerns

- Frontend purge changed comments/docs only (17 files, 68+/69-); no behavior change.
- `.agents/` program records and `.worktrees/` are intentionally excluded from the audit as history; they legitimately document the removed legacy files.
- `PLATFORM_SETUP.md` retains the phrase "legacy static UI" conceptually (no literal path token) — acceptable; the server no longer references it.
