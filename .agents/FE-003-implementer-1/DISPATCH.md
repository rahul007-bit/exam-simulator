# DISPATCH — FE-003

## 2026-09-10T06:17:42Z
You are assigned task **FE-003** on branch `feature/frontend-vue-migration`.

Working directory for metadata:
`.agents/FE-003-implementer-1`

Project workspace:
`C:/Users/HP/Projects/4-sep-test/cka-labs`

### Deliverable
`web/server.py` serves the built SPA `web/dist` with an SPA fallback; `/admin`
routes to the SPA; the build is wired into `tools/start-web.sh` (and the systemd
unit / platform setup docs).

### Acceptance criteria
1. `GET /` and `GET /admin` return the SPA index.
2. All existing `/api` and `/ws` routes unchanged and registered before the SPA
   catch-all (so they take precedence).
3. The `/novnc` StaticFiles mount is preserved.
4. Build on deploy produces `web/dist` without committing it.

### Verification method
On the platform host (Linux + Node/npm + backend deps):
```bash
python scripts/agents_board.py --check
python -m py_compile web/server.py
python .agents/FE-003-implementer-1/route_order_audit.py
tools/build-frontend.sh                      # produces web/dist/index.html
# start server, then:
curl -s localhost:3000/        | head        # SPA index (<div id="app">, /assets/)
curl -s localhost:3000/admin   | head        # SPA index
curl -s -o /dev/null -w '%{http_code}' localhost:3000/api/session   # 200
curl -s -o /dev/null -w '%{http_code}' localhost:3000/novnc/        # mount preserved
python scripts/verify_platform_api.py        # pass
git check-ignore web/dist/index.html         # ignored (D-005)
```

### Constraints
- One focused change.
- Preserve parity behavior (WS, clipboard, timer, token routing) — no handler edits.
- Update `EVIDENCE.md` with proof; set status in `tasks.json`.
- Do not commit/amend/push/open PRs.
