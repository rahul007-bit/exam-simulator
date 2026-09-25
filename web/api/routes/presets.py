import os
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from core.redis_bus import bus as redis_bus
from core.sandbox_orchestrator import orchestrator

from web.api.schemas import GeneratePresetRequest, PresetSelectRequest
from web.api.security import require_admin, require_user
from web.api.state import deployer, selector
from web.api.owner_lock import _claim_owner, _clear_owner, _client_id
from web.api.candidate_tokens import register_token
from web.api.services.preset_generator import generate_questions
from web.api.services.session_view import build_session_payload
from web.api.presets_info import _get_locked_preset_info, get_selected_preset_override, set_selected_preset_override
from web.api.session_ownership import record_session_owner
from web.api import auth_sessions

router = APIRouter()


@router.get("/api/presets")
def get_presets(request: Request):
    """Lists the preset catalog (admin only)."""
    require_admin(request)
    presets = selector.list_presets()
    for p in presets:
        if "task_count" not in p:
            p["task_count"] = len(p.get("questions", []))
    default_cfg = redis_bus.get_default_preset() if redis_bus.is_available() else "mock-01-acme"
    selected = get_selected_preset_override() or default_cfg or os.getenv("EXAM_PRESET") or "mock-01-acme"

    return {"presets": presets, "selected": selected}


@router.post("/api/presets/select")
def select_preset(req: PresetSelectRequest, request: Request):
    """Sets the global default preset override (admin only)."""
    require_admin(request)
    set_selected_preset_override(req.preset)
    return {"status": "ok", "preset": req.preset, "info": _get_locked_preset_info(req.preset)}


@router.post("/api/presets/generate")
def generate_preset(req: GeneratePresetRequest, request: Request):
    """Generates an ephemeral preset on the fly and starts a session for it (any signed-in user)."""
    require_user(request)
    try:
        questions = generate_questions(req.count, difficulty=req.difficulty, domains=req.domains)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # FS-003b: replace only the caller's own previous session.
    from web.api.session_resolver import resolve_session_id

    prev_sid = resolve_session_id(request, allow_legacy_active=False)
    if prev_sid:
        try:
            redis_bus.archive_session(prev_sid, status="replaced")
            orchestrator.teardown_session(prev_sid)
            _clear_owner(prev_sid)
        except Exception:
            pass

    session = deployer.deploy_sequential(
        questions,
        session_name=f"Generated Exam ({len(questions)} Questions)",
        time_limit_minutes=None,
    )

    if session and session.session_id:
        token = secrets.token_urlsafe(16)
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
            owner_username = token

        session.owner_username = owner_username
        record_session_owner(session.session_id, owner_username)
        deployer.save_session(session)

        register_token(token, session.session_id)
        if redis_bus.is_available():
            try:
                redis_bus.set_session_state(session.session_id, session.to_dict())
                redis_bus.register_active_session(session.session_id, session.to_dict())
            except Exception:
                pass

        _claim_owner(session.session_id, _client_id(request))
        if resolved_username:
            redis_bus.set_user_active_session(resolved_username, session.session_id)
        redis_bus.touch_session_activity(session.session_id)
        orchestrator.provision_session(session.session_id, contexts=session.target_contexts)

        try:
            deployer.deploy_step(session, 0, force_setup=True)
        except Exception as ex:
            print(f"[PresetGenerate] Warning deploying initial Task 1: {ex}")

    return build_session_payload(request)
