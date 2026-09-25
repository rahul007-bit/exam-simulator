from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

from web.api.state import DIST_DIR, SPA_INDEX

router = APIRouter()


# Admin dashboard route. The unified Vue SPA owns /admin (it branches on
# ?admin=1 internally), so we serve the SPA index here. If no build is present
# the frontend is unavailable (FE-040 cutover).
@router.get("/admin", response_class=HTMLResponse)
def get_admin_page(request: Request):
    if SPA_INDEX.is_file():
        return HTMLResponse(content=SPA_INDEX.read_text(encoding="utf-8"))
    raise HTTPException(status_code=503, detail="Frontend build missing; run tools/build-frontend.sh")


@router.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_fallback(full_path: str):
    # Never let an unknown API/WS/novnc path resolve to index.html.
    head = full_path.split("/", 1)[0]
    if head in ("api", "ws", "novnc"):
        raise HTTPException(status_code=404, detail="Not found")

    # Serve a real built file when one exists (hashed assets are mounted
    # separately above; this also covers favicon.svg / robots.txt / etc.).
    if full_path:
        candidate = (DIST_DIR / full_path).resolve()
        in_dist = candidate.is_relative_to(DIST_DIR.resolve())
        if in_dist and candidate.is_file():
            return FileResponse(candidate)

    # SPA fallback: hand index.html to the Vue router for any app route
    # (/, /admin, /login, /dashboard, /exam/:id, ...).
    if SPA_INDEX.is_file():
        return HTMLResponse(content=SPA_INDEX.read_text(encoding="utf-8"))

    raise HTTPException(status_code=503, detail="Frontend build missing; run tools/build-frontend.sh")
