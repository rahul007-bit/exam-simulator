import secrets
import time
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core.recorder import recorder
from core.redis_bus import bus as redis_bus, get_system_resource_info
from core.sandbox_orchestrator import orchestrator

from web.api.schemas import FlagRequest, JumpRequest, StartRequest
from web.api.state import deployer, loader, selector
from web.api.security import is_admin_authenticated
from web.api.owner_lock import _claim_owner, _clear_owner, _client_id, _enforce_owner
from web.api.candidate_tokens import register_token, resolve_token_sid
from web.api.services.session_view import build_session_payload
from web.api.services.submit import perform_submit
from web.api.session_ownership import record_session_owner
from web.api import auth_sessions

router = APIRouter()


def _make_progress_cb(session_id: str):
    def cb(stage: str, title: str, step: int, total_steps: int, desc: str = ""):
        try:
            redis_bus.publish_session_event(session_id, {
                "type": "transition_progress",
                "stage": stage,
                "title": title,
                "desc": desc,
                "step": step,
                "total_steps": total_steps,
                "percent": int((step / total_steps) * 100),
            })
        except Exception:
            pass
    return cb


@router.get("/api/questions")
def get_questions(request: Request):
    session = deployer.load_active_session(loader)
    if not session:
        return {"questions": []}
    _enforce_owner(request, session.session_id)

    questions_list = []
    for idx, q in enumerate(session.questions):
        questions_list.append({
            "task_num": idx + 1,
            "id": q.id,
            "title": q.title,
            "domain": q.domain.value if hasattr(q.domain, "value") else str(q.domain),
            "difficulty": q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
            "points": q.points,
            "target_context": q.target_context,
            "namespace": q.namespace or "default",
            "is_current": idx == session.current_index,
            "is_flagged": q.id in session.flagged,
            "score_data": session.scores.get(q.id),
        })

    return {"questions": questions_list, "total": len(questions_list)}


@router.post("/api/start")
def start_exam(req: StartRequest, request: Request):
    cid = _client_id(request)
    cand_tok = req.candidate_token
    # If candidate token is provided, check if session already active for it
    if cand_tok:
        existing_sid = resolve_token_sid(cand_tok)
        if existing_sid:
            existing_session = deployer.load_session(loader, existing_sid)
            if existing_session and existing_session.status == "active":
                return build_session_payload(request)

    # Resource check before starting a new session / container
    # FS-003b: only the caller's OWN previous session is replaced; other users'
    # sessions keep running concurrently (bounded by max_concurrent_sessions).
    from web.api.session_resolver import resolve_session_id

    caller_sid = resolve_session_id(request, allow_legacy_active=False)
    old_session = deployer.load_session(loader, caller_sid) if caller_sid else None
    res_info = get_system_resource_info()
    running = res_info["running_containers"]
    max_sessions = res_info["max_concurrent_sessions"]
    if running >= max_sessions:
        raise HTTPException(
            status_code=429,
            detail=f"Server resource limit reached: Maximum concurrent sessions ({max_sessions}) currently active ({running} running). Please wait for an active session to finish or contact the administrator."
        )

    # Archive the caller's OWN previous session (if any) before replacing it.
    if old_session and old_session.session_id:
        try:
            redis_bus.archive_session(old_session.session_id, status="replaced")
            orchestrator.teardown_session(old_session.session_id)
            _clear_owner(old_session.session_id)
        except Exception:
            pass

    # Preset selection: request preset > candidate invitation preset > global default
    preset_name = req.preset
    if cand_tok and not preset_name:
        inv = redis_bus.get_invitation(cand_tok)
        if inv and inv.get("preset"):
            preset_name = inv.get("preset")

    if not preset_name:
        preset_name = redis_bus.get_default_preset()

    if req.all_questions or preset_name == "all":
        questions = loader.get_all()
        session = deployer.deploy_sequential(
            questions,
            session_name="Full Curriculum (111 Tasks)",
            time_limit_minutes=None,
        )
    elif req.question_ids:
        questions = [loader.get(qid) for qid in req.question_ids if loader.get(qid) is not None]
        if not questions:
            raise HTTPException(status_code=400, detail="No valid questions found for given IDs")
        session = deployer.deploy_sequential(
            questions,
            session_name=f"Selected Practice Tasks ({len(questions)} Questions)",
            time_limit_minutes=None,
        )
    else:
        preset_data = selector.load_preset(preset_name)
        if not preset_data:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
        q_ids = preset_data.get("questions", [])
        questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
        session = deployer.deploy_sequential(
            questions,
            session_name=preset_data.get("name", preset_name),
            time_limit_minutes=preset_data.get("time_limit_minutes", 120),
        )

    if session and session.session_id:
        token = cand_tok or secrets.token_urlsafe(16)
        session.candidate_token = token
        session.status = "active"
        session.last_active_at = datetime.now(timezone.utc).isoformat()

        owner_username = None
        resolved_username = None
        try:
            resolved = auth_sessions.resolve_session(request)
            if resolved:
                resolved_username = resolved.get("username")
                owner_username = resolved_username
        except Exception:
            resolved_username = None
        if not owner_username:
            owner_username = cand_tok

        assigned_by = None
        if cand_tok:
            try:
                invitation = redis_bus.get_invitation(cand_tok)
                if invitation:
                    assigned_by = invitation.get("assigned_by") or None
            except Exception:
                assigned_by = None

        session.owner_username = owner_username
        session.assigned_by = assigned_by
        record_session_owner(session.session_id, owner_username, assigned_by)
        deployer.save_session(session)

        # Register token -> session_id mapping in memory and Redis
        register_token(token, session.session_id)
        if redis_bus.is_available():
            try:
                redis_bus.set_session_state(session.session_id, session.to_dict())
                redis_bus.register_active_session(session.session_id, session.to_dict())
                redis_bus.get_sync_client().set(
                    "session:active:id", session.session_id, ex=86400
                )
                if cand_tok:
                    redis_bus.update_invitation(cand_tok, {
                        "status": "started",
                        "session_id": session.session_id,
                        "started_at": time.time(),
                    })
            except Exception:
                pass

        _claim_owner(session.session_id, cid)
        if resolved_username:
            redis_bus.set_user_active_session(resolved_username, session.session_id)
        redis_bus.touch_session_activity(session.session_id)
        orchestrator.provision_session(session.session_id, contexts=session.target_contexts)

        # Deploy Task 1 now that k3d-cka cluster exists and host ~/.kube/config is populated!
        try:
            deployer.deploy_step(session, 0, force_setup=True)
        except Exception as ex:
            print(f"[StartExam] Warning deploying initial Task 1: {ex}")

    return build_session_payload(request)


@router.post("/api/action/next")
def action_next(request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")
    _enforce_owner(request, session.session_id)

    next_idx = session.current_index + 1
    if next_idx >= len(session.questions):
        raise HTTPException(status_code=400, detail="Already at the final task")

    deployer.deploy_step(session, next_idx, progress_cb=_make_progress_cb(session.session_id))
    return build_session_payload(request)


@router.post("/api/action/prev")
def action_prev(request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")
    _enforce_owner(request, session.session_id)

    prev_idx = session.current_index - 1
    if prev_idx < 0:
        raise HTTPException(status_code=400, detail="Already at the first task")

    deployer.deploy_step(session, prev_idx, progress_cb=_make_progress_cb(session.session_id))
    return build_session_payload(request)


@router.post("/api/action/jump")
def action_jump(req: JumpRequest, request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")
    _enforce_owner(request, session.session_id)

    target_idx = req.task_num - 1
    if target_idx < 0 or target_idx >= len(session.questions):
        raise HTTPException(status_code=400, detail=f"Task number {req.task_num} out of range")

    actor = "admin" if is_admin_authenticated(request) else "candidate"
    try:
        recorder.attach_or_resume(session.session_id, session.name)
        recorder.log_event("TASK_JUMP", {"task_num": req.task_num, "actor": actor}, actor=actor)
    except Exception:
        pass

    deployer.deploy_step(session, target_idx, progress_cb=_make_progress_cb(session.session_id))
    return build_session_payload(request)


@router.post("/api/action/flag")
def action_flag(req: FlagRequest, request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.questions:
        raise HTTPException(status_code=400, detail="No active exam session")
    _enforce_owner(request, session.session_id)

    idx = (req.task_num - 1) if req.task_num is not None else session.current_index
    if idx < 0 or idx >= len(session.questions):
        raise HTTPException(status_code=400, detail="Invalid task index")

    target_q = session.questions[idx]
    if target_q.id in session.flagged:
        session.flagged.remove(target_q.id)
        is_flagged = False
    else:
        session.flagged.append(target_q.id)
        is_flagged = True

    deployer.save_session(session)
    try:
        recorder.attach_or_resume(session.session_id, session.name)
        recorder.log_event("TASK_FLAGGED" if is_flagged else "TASK_UNFLAGGED", {
            "task_num": idx + 1,
            "question_id": target_q.id,
            "title": target_q.title,
            "is_flagged": is_flagged,
        })
    except Exception:
        pass
    return {"id": target_q.id, "task_num": idx + 1, "is_flagged": is_flagged, "flagged_ids": session.flagged}


@router.post("/api/action/retry")
def action_retry(request: Request):
    session = deployer.load_active_session(loader)
    if not session or not session.current_question:
        raise HTTPException(status_code=400, detail="No active question to retry")
    _enforce_owner(request, session.session_id)

    cur_idx = session.current_index
    actor = "admin" if is_admin_authenticated(request) else "candidate"
    try:
        cur_q = session.current_question
        recorder.attach_or_resume(session.session_id, session.name)
        recorder.log_event("TASK_RETRY", {
            "task_num": cur_idx + 1,
            "question_id": cur_q.id if cur_q else None,
            "title": cur_q.title if cur_q else None,
            "actor": actor,
        }, actor=actor)
    except Exception:
        pass
    # Re-run deploy step for current index with forced setup reset
    deployer.deploy_step(session, cur_idx, force_setup=True, progress_cb=_make_progress_cb(session.session_id))
    return {"status": "ok", "message": f"Task {cur_idx + 1} re-initialized"}


@router.post("/api/action/submit")
def action_submit(request: Request):
    return perform_submit(request)


@router.post("/api/reset")
def reset_exam(request: Request):
    actor = "admin" if is_admin_authenticated(request) else "candidate"
    active_session = deployer.load_active_session(loader)
    if active_session and active_session.session_id:
        _enforce_owner(request, active_session.session_id)
        try:
            recorder.attach_or_resume(active_session.session_id, active_session.name)
            recorder.log_event("EXAM_RESET", {"actor": actor}, actor=actor)
        except Exception:
            pass
        redis_bus.archive_session(active_session.session_id, status="reset")
        orchestrator.teardown_session(active_session.session_id)
        _clear_owner(active_session.session_id)
    deployer.clear_session(cleanup_cluster=True)
    return {"status": "ok", "message": "Exam session cleared and cluster cleaned"}


@router.post("/api/end")
def end_exam(request: Request):
    return reset_exam(request)
