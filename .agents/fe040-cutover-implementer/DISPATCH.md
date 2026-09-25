# DISPATCH — FE-040 (part 2: cutover)

## 2026-09-10T18:09:58Z
You are assigned task **FE-040 (legacy removal and static cutover)** — part 2, the
cutover half — on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/fe040-cutover-implementer`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
Delete the legacy UI and serve **only** the built SPA (`web/dist`): remove
`web/static/**`, rewrite `web/server.py` so all non-API routes are served from
`web/dist` (503 when the build is absent), update tools/docs, and add a backend
cutover regression test.

### Acceptance criteria
1. Legacy files deleted (`web/static/**`), staged via `git rm -r`.
2. All app routes (`/`, `/admin`, `/login`, …) serve from `web/dist`; no dead
   `web/static`/`admin.html`/`STATIC_DIR` references remain.
3. Unknown `api`/`ws`/`novnc` paths return 404 (never index.html).
4. `tools/build-frontend.sh` / `tools/start-web.sh` / `PLATFORM_SETUP.md` no
   longer advertise a legacy `web/static` fallback.
5. `tests/test_frontend_cutover.py` passes (host-only leg skipped on Windows).

### Verification method
- `python tests/test_frontend_cutover.py -v`
- `python -m py_compile web/server.py`
- `git grep -n -E 'web/static|static/js|static/css|app\.js|admin\.js|admin\.html|style\.css' -- . ':(exclude).agents' ':(exclude).worktrees'` → zero hits

### Constraints
- Do NOT touch `web/frontend/**` (part 1 already purged it), `core/**`, `docker/**`.
- No commit/amend/push; do not run `bun run build` / Playwright / agents_board.py.
- Preserve parity behavior (WS, clipboard, timer, token routing).
