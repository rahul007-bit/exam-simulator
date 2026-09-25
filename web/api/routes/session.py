import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core.models import ExamSession
from core.recorder import recorder
from core.redis_bus import bus as redis_bus, get_system_resource_info
from core.sandbox_orchestrator import orchestrator

from web.api.schemas import RestoreSessionRequest
from web.api.state import BASE_DIR, deployer, loader
from web.api.security import is_admin_authenticated
from web.api.owner_lock import _claim_owner, _client_id, _enforce_owner
from web.api.candidate_tokens import register_token
from web.api.desktop_restore import is_container_running
from web.api.exam_helpers import _calculate_time_remaining
from web.api.services.session_view import build_session_payload
from web.api.session_ownership import record_session_owner

router = APIRouter()


@router.get("/api/session")
def get_session(request: Request):
    return build_session_payload(request)


@router.get("/api/timer")
def get_timer(request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.session_id:
        return {"active": False, "time_remaining_seconds": None}
    _enforce_owner(request, session.session_id)
    try:
        time_limit = session.time_limit_minutes
        created_at = session.created_at
        if not time_limit:
            return {"active": True, "time_remaining_seconds": None, "time_limit_minutes": None}

        created_str = (created_at or "").replace("Z", "+00:00")
        created_dt = datetime.fromisoformat(created_str)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=timezone.utc)
        now_dt = datetime.now(timezone.utc)
        start_ts = created_dt.timestamp()
        total = time_limit * 60
        end_ts = start_ts + total
        remaining = max(0, int(end_ts - now_dt.timestamp()))
        elapsed = int(now_dt.timestamp() - start_ts)
        return {
            "active": True,
            "session_id": session.session_id,
            "started_at": created_dt.isoformat(),
            "start_timestamp": start_ts,
            "end_timestamp": end_ts,
            "server_timestamp": now_dt.timestamp(),
            "time_limit_minutes": time_limit,
            "total_seconds": total,
            "elapsed_seconds": elapsed,
            "time_remaining_seconds": remaining,
        }
    except Exception as e:
        return {"active": False, "error": str(e)}


@router.post("/api/session/restore")
def restore_session(req: RestoreSessionRequest, request: Request):
    session_id = req.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    cid = _client_id(request)

    # Check resource limit before restoring
    res_info = get_system_resource_info()
    running = res_info["running_containers"]
    max_sessions = res_info["max_concurrent_sessions"]
    avail_mem = res_info["available_mem_mb"]

    is_already_running = is_container_running(session_id)
    effective_running = (running - 1) if is_already_running else running

    if effective_running >= max_sessions or avail_mem < 350:
        raise HTTPException(
            status_code=429,
            detail=f"Server resource limit reached: Maximum concurrent sessions ({max_sessions}) currently active ({running} running). Please wait for an active session to finish or contact the administrator."
        )

    # Retrieve archived session from Redis history:{session_id} or file archive
    data = None
    if redis_bus.is_available():
        data = redis_bus.get_archived_session(session_id)
        if not data:
            try:
                raw = redis_bus.get_sync_client().get(f"session:{session_id}")
                if raw:
                    data = json.loads(raw)
            except Exception:
                pass

    if not data:
        archive_p = BASE_DIR / "var" / "archive" / f"{session_id}.json"
        if archive_p.exists():
            try:
                data = json.loads(archive_p.read_text(encoding="utf-8"))
            except Exception:
                pass

    if not data:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found in history or archive")

    q_ids = data.get("question_ids", [])
    questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]

    session = ExamSession(
        session_id=session_id,
        created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        name=data.get("name", "Restored Exam Session"),
        questions=questions,
        target_contexts=data.get("target_contexts", []),
        time_limit_minutes=data.get("time_limit_minutes"),
        mode=data.get("mode", "sequential"),
        current_index=data.get("current_index", 0),
        scores=data.get("scores", {}),
        flagged=data.get("flagged", []),
        scorecard=data.get("scorecard"),
        status="active",
        last_active_at=datetime.now(timezone.utc).isoformat(),
        candidate_token=data.get("candidate_token"),
        owner_username=data.get("owner_username"),
        assigned_by=data.get("assigned_by"),
    )
    if session.owner_username:
        record_session_owner(session.session_id, session.owner_username, session.assigned_by)

    # Revive session as active session in Redis & deployer.save_session
    deployer.save_session(session)
    if redis_bus.is_available():
        redis_bus.set_session_state(session_id, session.to_dict())
        redis_bus.register_active_session(session_id, session.to_dict())
        if session.candidate_token:
            register_token(session.candidate_token, session_id)
        redis_bus.touch_session_activity(session_id)

    # Enforce ownership before (re)claiming: a non-owner/non-admin must not be
    # able to overwrite the owner lock by restoring someone else's session.
    _enforce_owner(request, session_id)
    _claim_owner(session_id, cid)

    # Re-run full provisioning: after a teardown the Incus fleet VMs are gone,
    # so start_desktop alone would leave the desktop without ssh/kubectl access.
    orchestrator.provision_session(session_id, contexts=session.target_contexts)
    actor = "admin" if is_admin_authenticated(request) else "candidate"
    try:
        recorder.attach_or_resume(session_id, session.name)
        recorder.log_event("SESSION_RESTORED", {"session_id": session_id, "actor": actor}, actor=actor)
    except Exception:
        pass

    print(f"[SessionRestore] Restored and revived session {session_id}", flush=True)
    return build_session_payload(request)


@router.get("/api/sessions")
def list_sessions():
    """Returns session history (all past + current sessions) from Redis archive."""
    history = redis_bus.list_session_history(limit=50)
    # Also include every currently active session (FS-003b).
    for active_sid in redis_bus.list_active_session_ids():
        current = deployer.load_session(loader, active_sid)
        if not current or current.status != "active":
            continue
        history.insert(0, {
            "session_id": current.session_id,
            "name": current.name,
            "status": current.status or "active",
            "created_at": current.created_at,
            "archived_at": None,
            "total_tasks": len(current.questions),
            "time_limit_minutes": current.time_limit_minutes,
            "time_remaining_seconds": _calculate_time_remaining(current),
            "scorecard_summary": None,
            "candidate_token": current.candidate_token,
        })
    return {"sessions": history, "total": len(history)}
