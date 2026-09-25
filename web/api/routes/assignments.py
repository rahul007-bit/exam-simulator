import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core.redis_bus import bus as redis_bus
from web.api import auth_sessions, users
from web.api.security import require_admin
from web.api.state import selector

router = APIRouter()


class AssignmentCreateRequest(BaseModel):
    username: str
    preset: str


def _serialize(record: dict) -> dict:
    """Maps a stored invitation record to the assignment API shape."""
    created = record.get("created_at")
    created_at = ""
    if created:
        try:
            created_at = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            created_at = str(created)
    token = record.get("token", "")
    return {
        "id": token,
        "username": record.get("assigned_to", ""),
        "preset": record.get("preset", ""),
        "assigned_by": record.get("assigned_by", ""),
        "status": record.get("status", "pending"),
        "created_at": created_at,
        "url": f"/?token={token}" if token else "",
    }


@router.post("/api/admin/assignments")
def create_assignment(req: AssignmentCreateRequest, request: Request):
    """Assigns an exam preset to a named user (admin only)."""
    require_admin(request)
    if not users.get_user(req.username):
        raise HTTPException(status_code=400, detail=f"User '{req.username}' not found")
    if not selector.load_preset(req.preset):
        raise HTTPException(status_code=404, detail=f"Preset '{req.preset}' not found")

    resolved = auth_sessions.resolve_session(request)
    assigner = (resolved or {}).get("username") or "admin"
    token = secrets.token_urlsafe(16)
    record = redis_bus.create_invitation(
        token, req.preset, assigned_by=assigner, assigned_to=req.username
    )
    return {"status": "ok", "assignment": _serialize(record)}


@router.get("/api/admin/assignments")
def list_assignments(request: Request):
    """Lists every user-bound assignment (admin only)."""
    require_admin(request)
    assignments = [_serialize(record) for record in redis_bus.list_assignments()]
    return {"assignments": assignments, "total": len(assignments)}


@router.delete("/api/admin/assignments/{assignment_id}")
def delete_assignment(assignment_id: str, request: Request):
    """Deletes a user-bound assignment (admin only)."""
    require_admin(request)
    record = redis_bus.get_invitation(assignment_id)
    if not record or not record.get("assigned_to"):
        raise HTTPException(status_code=404, detail="Assignment not found")
    redis_bus.delete_assignment(assignment_id)
    return {"status": "ok", "id": assignment_id}


@router.get("/api/assignments")
def list_my_assignments(request: Request):
    """Lists the current user's own assignments."""
    session = auth_sessions.resolve_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    assignments = [
        _serialize(record) for record in redis_bus.get_user_assignments(session.get("username"))
    ]
    return {"assignments": assignments, "total": len(assignments)}
