from fastapi import APIRouter, HTTPException, Request

from core.recorder import recorder
from core.redis_bus import bus as redis_bus

from web.api.schemas import ClipboardRequest
from web.api.state import deployer, loader
from web.api.owner_lock import _enforce_owner
from web.api.clipboard_state import set_x11_clipboard

router = APIRouter()


@router.post("/api/clipboard")
def set_clipboard_endpoint(req: ClipboardRequest, request: Request):
    try:
        session = deployer.load_active_session(loader)
        if session and session.session_id:
            _enforce_owner(request, session.session_id)
        sid = session.session_id if session else "default"
        set_x11_clipboard(req.text)
        redis_bus.set_clipboard(sid, req.text)
        if session:
            try:
                recorder.attach_or_resume(session.session_id, session.name)
                recorder.log_event("CLIPBOARD_COPY", {
                    "length": len(req.text),
                    "preview": req.text[:120],
                })
            except Exception:
                pass
        return {"status": "ok", "length": len(req.text)}
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/api/clipboard")
def get_clipboard_endpoint(request: Request):
    try:
        session = deployer.load_active_session(loader)
        if session and session.session_id:
            _enforce_owner(request, session.session_id)
        sid = session.session_id if session else "default"
        text = redis_bus.get_clipboard(sid)
        return {"text": text}
    except HTTPException:
        raise
    except Exception as e:
        return {"text": "", "error": str(e)}
