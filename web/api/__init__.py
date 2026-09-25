from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from web.api.state import DIST_DIR

NOVNC_DIR = Path("/usr/share/novnc")


def create_app() -> FastAPI:
    # Route modules are imported lazily so that importing a single route module
    # (e.g. web.api.routes.recordings in tests) never pulls in the host-only
    # websocket bridges (pty/fcntl/termios) on non-host platforms.
    from web.api import background
    from web.api import users
    from web.api.routes import (
        admin,
        assignments,
        auth,
        clipboard,
        exam,
        presets,
        recordings,
        session,
        spa,
        ws_desktop,
        ws_events,
        ws_terminal,
    )

    app = FastAPI(title="Kubernetes Exam Web Simulator", version="2.0.0")

    # Enable CORS for local development and embedded contexts
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Route ordering matters: every /api and /ws router (plus the static mounts
    # below) is registered before the SPA router, whose catch-all would
    # otherwise swallow them.
    app.include_router(session.router)
    app.include_router(exam.router)
    app.include_router(presets.router)
    app.include_router(clipboard.router)
    app.include_router(recordings.router)
    app.include_router(admin.router)
    app.include_router(auth.router)
    app.include_router(assignments.router)
    app.include_router(ws_terminal.router)
    app.include_router(ws_desktop.router)
    app.include_router(ws_events.router)

    # Mount noVNC static files if present
    if NOVNC_DIR.exists():
        app.mount("/novnc", StaticFiles(directory=str(NOVNC_DIR), html=True), name="novnc")

    # Built SPA (web/dist) static assets (FE-003)
    if (DIST_DIR / "assets").is_dir():
        app.mount(
            "/assets",
            StaticFiles(directory=str(DIST_DIR / "assets")),
            name="assets",
        )

    # The SPA router (/admin + catch-all) must be included LAST (see above).
    app.include_router(spa.router)

    # Background workers: host clipboard, timer broadcast, idle reaper, expiry
    @app.on_event("startup")
    async def _startup_workers():
        try:
            users.ensure_bootstrap_admin()
        except Exception as ex:
            print(f"[Startup] Bootstrap admin error: {ex}", flush=True)
        await background.start_background_workers()

    return app
