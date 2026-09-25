import json
import secrets
import subprocess
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from core.recorder import recorder
from web.api.schemas import ClientEventRequest
from web.api.state import REPORTS_DIR

router = APIRouter()


@router.get("/api/reports")
def list_reports():
    if not REPORTS_DIR.exists():
        return {"reports": []}
    files = sorted(REPORTS_DIR.glob("report-*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    res = []
    for f in files:
        try:
            with open(f) as fp:
                data = json.load(fp)
                res.append({
                    "filename": f.name,
                    "session_id": data.get("session_id"),
                    "exam_name": data.get("exam_name"),
                    "submitted_at": data.get("submitted_at"),
                    "percentage": data.get("percentage"),
                    "passed": data.get("passed"),
                    "score": f"{data.get('total_earned')}/{data.get('total_possible')}",
                    "md_file": f"report-{data.get('session_id')}.md",
                })
        except Exception:
            pass
    return {"reports": res}


@router.get("/api/reports/{filename}")
def get_report(filename: str):
    file_path = REPORTS_DIR / filename
    if not file_path.is_file() or not file_path.resolve().is_relative_to(REPORTS_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Report not found")
    media_type = "application/json" if filename.endswith(".json") else "text/markdown"
    return FileResponse(file_path, media_type=media_type, filename=filename)


@router.get("/api/recordings")
def list_recordings_endpoint():
    recs = recorder.list_recordings()
    return {"recordings": recs, "total": len(recs)}


@router.get("/api/recordings/{session_id}")
def get_recording_detail_endpoint(session_id: str):
    data = recorder.get_recording(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Recording not found")
    return data


@router.get("/api/recordings/{session_id}/cast")
def get_recording_cast_endpoint(session_id: str, channel: str = "user-web"):
    cast_path = recorder.get_cast_path(session_id, channel)
    if not cast_path or not cast_path.is_file():
        raise HTTPException(status_code=404, detail="Asciinema cast recording not found")
    return FileResponse(
        cast_path,
        media_type="application/x-asciicast",
        filename=f"{session_id}.{channel}.cast",
    )


@router.get("/api/recordings/{session_id}/events")
def get_recording_events_endpoint(session_id: str):
    events = recorder.get_events(session_id)
    return {"session_id": session_id, "events": events, "total": len(events)}


@router.post("/api/recordings/{session_id}/event")
def log_client_event_endpoint(session_id: str, req: ClientEventRequest):
    try:
        recorder.attach_or_resume(session_id)
        recorder.log_event(req.event_type, req.data or {})
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
