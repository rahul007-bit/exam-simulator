import json
import secrets
import subprocess
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from core.desktop_manager import desktop_mgr
from core.incus_manager import incus_mgr
from core.recorder import recorder
from core.redis_bus import bus as redis_bus, get_system_resource_info
from core.sandbox_orchestrator import orchestrator
from web.api.desktop_restore import is_container_running
from web.api.exam_helpers import _calculate_time_remaining
from web.api.owner_lock import _clear_owner
from web.api.presets_info import clear_selected_preset_override
from web.api.schemas import (
    AdminConfigRequest,
    AdminLoginRequest,
    CreateSessionInviteRequest,
    SetResourceLimitRequest,
    TerminateResourceRequest,
)
from web.api.security import (
    ADMIN_PASSWORD,
    is_admin_authenticated,
    issue_admin_token,
    revoke_admin_token,
)
from web.api.services.submit import perform_submit
from web.api.state import deployer, loader
from web.api import auth_sessions

router = APIRouter()

# --- Admin Plane Endpoints ---

@router.post("/api/admin/login")
def admin_login(req: AdminLoginRequest, response: Response):
    if req.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid admin password")
    token = issue_admin_token()
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        max_age=86400 * 7,
        path="/",
        samesite="lax",
    )
    return {"status": "ok", "token": token, "authenticated": True}


@router.get("/api/admin/check")
def admin_check(request: Request):
    return {"authenticated": is_admin_authenticated(request)}


@router.post("/api/admin/logout")
def admin_logout(request: Request, response: Response):
    cookie_token = request.cookies.get("admin_token")
    if cookie_token:
        revoke_admin_token(cookie_token)
    auth_header = request.headers.get("authorization", "") or request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        t = auth_header[7:].strip()
        revoke_admin_token(t)
    response.delete_cookie(key="admin_token", path="/")
    return {"status": "ok", "authenticated": False}


@router.get("/api/admin/config")
def admin_get_config(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    preset = redis_bus.get_default_preset()
    return {"default_preset": preset}


@router.post("/api/admin/config")
def admin_set_config(req: AdminConfigRequest, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    redis_bus.set_default_preset(req.default_preset)
    clear_selected_preset_override()
    return {"status": "ok", "default_preset": req.default_preset}


@router.get("/api/admin/resources")
def admin_get_resources(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return get_system_resource_info()


@router.post("/api/admin/resources")
def admin_set_resources(req: SetResourceLimitRequest, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if req.max_concurrent_sessions < 1:
        raise HTTPException(status_code=400, detail="max_concurrent_sessions must be at least 1")
    redis_bus.set_max_concurrent_sessions(req.max_concurrent_sessions)
    return get_system_resource_info()


@router.post("/api/admin/sessions/create")
def admin_create_session_invite(req: CreateSessionInviteRequest, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    res_info = get_system_resource_info()
    if res_info["running_containers"] >= res_info["max_concurrent_sessions"] or res_info["available_mem_mb"] < 350:
        raise HTTPException(
            status_code=429,
            detail=f"Server resource limit reached: Maximum concurrent sessions ({res_info['max_concurrent_sessions']}) currently active ({res_info['running_containers']} running). Please wait for an active session to finish or contact the administrator."
        )

    preset = req.preset or redis_bus.get_default_preset()
    token = secrets.token_urlsafe(16)
    resolved = auth_sessions.resolve_session(request)
    assigner = (resolved or {}).get("username") or "admin"
    redis_bus.create_invitation(token, preset, assigned_by=assigner)
    return {
        "token": token,
        "preset": preset,
        "url": f"/?token={token}",
    }


@router.get("/api/admin/sessions")
def admin_list_sessions(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    items = []
    seen_tokens = set()
    seen_sids = set()

    # 1. Active sessions (FS-003b: all live sessions, not just one)
    for active_sid in redis_bus.list_active_session_ids():
        active_s = deployer.load_session(loader, active_sid)
        if not active_s or active_s.status != "active":
            continue
        sid = active_s.session_id
        seen_sids.add(sid)
        if active_s.candidate_token:
            seen_tokens.add(active_s.candidate_token)
        rem = _calculate_time_remaining(active_s)
        items.append({
            "session_id": sid,
            "candidate_token": active_s.candidate_token,
            "name": active_s.name,
            "status": "active",
            "created_at": active_s.created_at,
            "time_remaining_seconds": rem,
            "container_running": is_container_running(sid),
            "total_tasks": len(active_s.questions),
            "current_index": active_s.current_index,
            "type": "active",
            "url": f"/?token={active_s.candidate_token}" if active_s.candidate_token else "/",
            "owner_username": active_s.owner_username,
            "assigned_by": active_s.assigned_by,
        })

    # 2. Invitations
    invitations = redis_bus.list_invitations()
    now_ts = time.time()
    for inv in invitations:
        token = inv.get("token")
        status = inv.get("status", "pending")
        created_ts = inv.get("created_at") or now_ts

        # Automatically expire pending invites older than 24 hours (86400s)
        if status == "pending" and (now_ts - created_ts > 86400):
            status = "expired"
            try:
                redis_bus.update_invitation(token, {"status": "expired"})
            except Exception:
                pass

        if status in ("pending", "expired") or (token not in seen_tokens and status != "started"):
            seen_tokens.add(token)
            created_str = datetime.fromtimestamp(created_ts, tz=timezone.utc).isoformat() if created_ts else ""
            items.append({
                "session_id": None,
                "candidate_token": token,
                "name": inv.get("preset", "Default Preset"),
                "status": status,
                "created_at": created_str,
                "time_remaining_seconds": None,
                "container_running": False,
                "total_tasks": None,
                "current_index": None,
                "type": "invite",
                "url": f"/?token={token}",
                "owner_username": None,
                "assigned_by": inv.get("assigned_by"),
            })

    # 3. History
    history = redis_bus.list_session_history(limit=50)
    for h in history:
        sid = h.get("session_id")
        if sid and sid not in seen_sids:
            seen_sids.add(sid)
            tok = h.get("candidate_token")
            if tok:
                seen_tokens.add(tok)
            items.append({
                "session_id": sid,
                "candidate_token": tok,
                "name": h.get("name", "Exam Session"),
                "status": h.get("status", "completed"),
                "created_at": h.get("created_at", ""),
                "archived_at": h.get("archived_at"),
                "time_remaining_seconds": 0,
                "container_running": is_container_running(sid),
                "total_tasks": h.get("total_tasks", 0),
                "scorecard_summary": h.get("scorecard_summary"),
                "type": "archived",
                "url": f"/?token={tok}" if tok else None,
                "owner_username": h.get("owner_username"),
                "assigned_by": h.get("assigned_by"),
            })

    return {"sessions": items, "total": len(items)}


@router.get("/api/admin/session/{session_id}")
def admin_get_session_detail(session_id: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    state = redis_bus.get_session_state(session_id)
    if not state:
        current = deployer.load_active_session(loader)
        if current and current.session_id == session_id:
            state = current.to_dict()
    if not state and redis_bus.is_available():
        client = redis_bus.get_sync_client()
        raw = client.get(f"history:{session_id}")
        if raw:
            try:
                state = json.loads(raw)
            except Exception:
                pass

    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    q_ids = state.get("question_ids", [])
    questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
    cur_idx = state.get("current_index", 0)
    current_q = questions[cur_idx] if 0 <= cur_idx < len(questions) else None

    task_data = None
    if current_q:
        task_data = {
            "task_num": cur_idx + 1,
            "id": current_q.id,
            "title": current_q.title,
            "domain": current_q.domain.value if hasattr(current_q.domain, "value") else str(current_q.domain),
            "difficulty": current_q.difficulty.value if hasattr(current_q.difficulty, "value") else str(current_q.difficulty),
            "points": current_q.points,
            "target_context": current_q.target_context,
            "namespace": current_q.namespace or "default",
            "description": current_q.description,
            "is_flagged": current_q.id in state.get("flagged", []),
            "score_data": state.get("scores", {}).get(current_q.id),
        }

    return {
        "session_id": session_id,
        "candidate_token": state.get("candidate_token"),
        "name": state.get("name"),
        "status": state.get("status", "active"),
        "current_index": cur_idx,
        "total_tasks": len(questions),
        "time_limit_minutes": state.get("time_limit_minutes"),
        "created_at": state.get("created_at"),
        "owner_username": state.get("owner_username"),
        "assigned_by": state.get("assigned_by"),
        "current_task": task_data,
        "container_running": is_container_running(session_id),
        "questions": [
            {
                "task_num": i + 1,
                "id": q.id,
                "title": q.title,
                "points": q.points,
                "is_current": i == cur_idx,
                "is_flagged": q.id in state.get("flagged", []),
                "score_data": state.get("scores", {}).get(q.id),
            }
            for i, q in enumerate(questions)
        ]
    }


class NotifySessionRequest(BaseModel):
    message: str


@router.post("/api/admin/sessions/{identifier}/notify")
def admin_notify_session(identifier: str, req: NotifySessionRequest, request: Request):
    """Sends an admin notification popup to the candidate's desktop (and web)."""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    actual_session_id = identifier
    if redis_bus.is_available():
        try:
            tok_sid = redis_bus.get_sync_client().get(f"token:{identifier}")
            if tok_sid:
                actual_session_id = tok_sid.decode() if isinstance(tok_sid, bytes) else tok_sid
        except Exception:
            pass

    published = redis_bus.publish_notification(actual_session_id, message)
    try:
        recorder.attach_or_resume(actual_session_id)
        recorder.log_event(
            "ADMIN_NOTIFICATION",
            {"session_id": actual_session_id, "message": message, "actor": "admin"},
            actor="admin",
            channel="admin-web",
        )
    except Exception:
        pass
    return {"status": "ok", "session_id": actual_session_id, "published": published}


@router.post("/api/admin/sessions/{identifier}/terminate")
def admin_terminate_session(identifier: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        recorder.attach_or_resume(identifier)
        recorder.log_event("ADMIN_SESSION_TERMINATE", {"session_id": identifier, "actor": "admin"}, actor="admin")
    except Exception:
        pass

    # Resolve session_id if identifier is a candidate token
    actual_session_id = identifier
    if redis_bus.is_available():
        try:
            client = redis_bus.get_sync_client()
            tok_sid = client.get(f"token:{identifier}")
            if tok_sid:
                actual_session_id = tok_sid
        except Exception:
            pass

    redis_bus.archive_session(actual_session_id, status="terminated")
    orchestrator.teardown_session(actual_session_id)
    if actual_session_id != identifier:
        orchestrator.teardown_session(identifier)

    active_s = deployer.load_active_session(loader)
    if active_s and (active_s.session_id == actual_session_id or active_s.session_id == identifier):
        deployer.clear_session(cleanup_cluster=True)

    redis_bus.delete_invitation(identifier)
    _clear_owner(actual_session_id)
    _clear_owner(identifier)
    if redis_bus.is_available():
        try:
            client = redis_bus.get_sync_client()
            client.delete(f"history:{identifier}")
            client.delete(f"history:{actual_session_id}")
            client.delete(f"token:{identifier}")
            client.delete(f"session:{identifier}")
            client.delete(f"session:{actual_session_id}")
            client.delete(f"session:{identifier}:state")
            client.delete(f"session:{actual_session_id}:state")
        except Exception:
            pass
    return {"status": "ok", "message": f"Session or invite {identifier} deleted/terminated and all resources freed"}


@router.post("/api/admin/sessions/{identifier}/reset")
def admin_reset_session(identifier: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        recorder.attach_or_resume(identifier)
        recorder.log_event("ADMIN_EXAM_RESET", {"session_id": identifier, "actor": "admin"}, actor="admin")
    except Exception:
        pass

    actual_session_id = identifier
    if redis_bus.is_available():
        try:
            client = redis_bus.get_sync_client()
            tok_sid = client.get(f"token:{identifier}")
            if tok_sid:
                actual_session_id = tok_sid
        except Exception:
            pass

    redis_bus.archive_session(actual_session_id, status="reset")
    orchestrator.teardown_session(actual_session_id)
    if actual_session_id != identifier:
        orchestrator.teardown_session(identifier)
    _clear_owner(actual_session_id)
    _clear_owner(identifier)

    active_s = deployer.load_active_session(loader)
    if active_s and (active_s.session_id == actual_session_id or active_s.session_id == identifier):
        deployer.clear_session(cleanup_cluster=True)

    return {"status": "ok", "message": f"Session {identifier} reset and cluster cleaned"}


@router.post("/api/admin/sessions/{identifier}/end")
def admin_end_session(identifier: str, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        recorder.attach_or_resume(identifier)
        recorder.log_event("ADMIN_EXAM_END", {"session_id": identifier, "actor": "admin"}, actor="admin")
    except Exception:
        pass

    active_s = deployer.load_active_session(loader)
    scorecard = None
    if active_s and active_s.session_id == identifier:
        scorecard = perform_submit(request)
    else:
        redis_bus.archive_session(identifier, status="submitted")
        orchestrator.teardown_session(identifier)
        deployer.clear_active_session()
        _clear_owner(identifier)



    return {"status": "ok", "message": f"Session {identifier} ended and evaluated", "scorecard": scorecard}


@router.get("/api/admin/infrastructure")
def admin_get_infrastructure(request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    docker_containers = desktop_mgr.list_all_docker_containers()
    incus_instances = incus_mgr.list_all_fleet_instances()

    resources = []
    for d in docker_containers:
        resources.append(d)
    for i in incus_instances:
        resources.append(i)

    nodes = [
        {"name": "mgmt", "ip": "10.8.0.15", "role": "Management & Web", "status": "ONLINE"},
        {"name": "node1", "ip": "192.168.50.169", "role": "Compute Node 1", "status": "ONLINE"},
        {"name": "node2", "ip": "192.168.50.188", "role": "Compute Node 2", "status": "ONLINE"},
        {"name": "node3", "ip": "192.168.50.170", "role": "Compute Node 3", "status": "ONLINE"},
    ]

    return {
        "nodes": nodes,
        "resources": resources,
        "summary": {
            "total_nodes": len(nodes),
            "total_docker_containers": len(docker_containers),
            "total_incus_instances": len(incus_instances),
            "total_resources": len(resources)
        }
    }


@router.post("/api/admin/infrastructure/terminate")
def admin_terminate_resource(req: TerminateResourceRequest, request: Request):
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    if req.kind == "docker":
        try:
            subprocess.run(["docker", "rm", "-f", req.name], timeout=10, stdout=subprocess.DEVNULL)
            return {"status": "ok", "message": f"Docker container {req.name} removed"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif req.kind == "incus":
        rem = None if req.node in ("mgmt", "local", "127.0.0.1") else req.node
        success = incus_mgr.delete_node(req.name, remote_name=rem)
        if success:
            return {"status": "ok", "message": f"Incus instance {req.name} removed from {req.node}"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete {req.name} on {req.node}")
    else:
        raise HTTPException(status_code=400, detail="Invalid resource kind")
