# Backend Modularization Plan (option 2 → k8s-ready)

Written: 2026-09-11. Status: in progress. Off-board prep work (user decision).

## Goal

Split the 2,542-line `web/server.py` monolith into a **module-per-task** package
(`web/api/`) where every module has exactly one responsibility, with all shared
state centralized so nothing is process-local by accident. The module boundaries
are the **future microservice boundaries** — the end goal (user-stated) is
deployment via **Docker / Kubernetes for scale**, not systemd units.

## Target layout

```
web/
  server.py              # facade: app = create_app(); compat re-exports
  api/
    __init__.py          # create_app(): CORS, routers, mounts, startup hook
    state.py             # paths (BASE_DIR/DIST_DIR/REPORTS_DIR/...), core
                         # singletons (loader, selector, deployer, grader), env settings
    schemas.py           # ALL Pydantic request models (one place, shared)
    security.py          # admin auth primitives (password, token cache+Redis verify)
    owner_lock.py        # soft per-session owner lock (Redis)
    candidate_tokens.py  # candidate token <-> session_id resolution (Redis-backed)
    desktop_restore.py   # node-bound container cache / auto-restore helpers
    presets_info.py      # preset override (Redis-backed) + locked preset info
    clipboard_state.py   # X11 clipboard mirror (get/set; node-local)
    exam_helpers.py      # time-remaining calc, task data formatting
    services/
      session_view.py    # build_session_payload(request) — the GET /api/session body
      submit.py          # perform_submit(request) — grading + report persistence
    background.py        # startup hook + 4 workers (X11 clipboard, timer broadcast,
                         # idle reaper, expiry enforcer)
    routes/
      session.py         # /api/session, /api/session/restore, /api/sessions, /api/timer
      exam.py            # /api/start, /api/questions, /api/action/*, /api/reset, /api/end
      presets.py         # /api/presets, /api/presets/select
      clipboard.py       # /api/clipboard (GET/POST)
      recordings.py      # /api/reports*, /api/recordings*
      admin.py           # /api/admin/*
      ws_terminal.py     # /ws/terminal (host pty bridge — node-bound)
      ws_desktop.py      # VNC/noVNC/websockify proxies
      ws_events.py       # /ws/session/{sid} pubsub bridge
      spa.py             # /admin page, /assets + /novnc mounts, SPA catch-all
```

## k8s end-goal mapping (how modules become services)

| Module group | Future service | Scaling note |
|---|---|---|
| routes/session + exam + presets + admin + recordings, services/ | stateless API pods (1–N replicas) | pure Redis/HTTP; scale horizontally |
| ws_terminal, ws_desktop, ws_events, background X11 monitor, desktop_restore | node-bound gateway (DaemonSet or host service) | needs pty, docker CLI, X11 on the node running the desktop containers |
| spa.py | Traefik/nginx static + CDN | no app server needed |
| state.py singletons (loader/selector) | read-only configmaps/persistent volume | questions/presets/sets are static content |

Rules that keep the split possible:
1. **No new process-local state.** Everything mutable goes to Redis (already true
   for sessions, invitations, admin tokens, candidate tokens, desktop info).
   In-process caches are allowed only as TTL caches over a Redis source of truth.
2. **Config only from env vars.**
3. **Cross-route calls go through `services/`, never route→route imports.**
4. **Node-bound code (pty, docker CLI, xsel, /etc writes) stays isolated** in
   ws_terminal / desktop_restore / background — the modules that will not scale out.

## Option-2 state moves (this refactor)

- `_selected_preset_override` — memory-only today → **Redis key `preset:override`**
  (with in-memory fallback when Redis is down). Affects presets + admin config.
- `_admin_tokens` / `_candidate_token_map` — already Redis-backed; keep in-process
  copies as fast-path caches (documented, safe for multi-replica).
- `_last_x11_clipboard` — node-local X11 mirror; moved behind
  `clipboard_state.get/set()` (never assumed shared).

## Constraints (do not break)

- `core/cli.py:481` runs `uvicorn.run("web.server:app")` — `web/server.py` must
  keep exposing `app`.
- `tests/test_recorder.py` imports recording endpoints + `ClientEventRequest`
  (test updated → `web.api.routes.recordings` / `web.api.schemas`).
- `tests/test_session_owner_lock.py` AST-extracts the 6 owner-lock helpers
  (test updated → `web/api/owner_lock.py`).
- `tests/test_frontend_cutover.py` greps source (test updated → spa.py facade).
- Host deploy verification: `.venv/bin/python -c 'import web.server'` +
  `k8s-web.service` restart must keep working (facade guarantees import path).
- Route registration order matters: all /api + /ws routes BEFORE the SPA
  catch-all; /novnc mount before catch-all (spa.py must be included last).

## Execution

Parallel batch (PROTOCOL §9 style, off-board):
1. Orchestrator creates shared foundation (state, schemas, security, owner_lock,
   candidate_tokens, desktop_restore, presets_info, clipboard_state,
   exam_helpers, services/, __init__ skeleton).
2. 3 agents in parallel, disjoint files:
   - A: services bodies + routes/session.py + exam.py + presets.py + clipboard.py
   - B: routes/admin.py + routes/recordings.py
   - C: routes/ws_terminal.py + ws_desktop.py + ws_events.py + spa.py + background.py
3. Orchestrator: facade `web/server.py`, test updates, consolidated verification
   (`py_compile` all → unit tests → host import check + deploy later with FE-044).
