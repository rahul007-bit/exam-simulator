import os
from datetime import datetime, timezone

from core.redis_bus import bus as redis_bus

from web.api.state import deployer, loader
from web.api.security import is_admin_authenticated
from web.api.owner_lock import _client_id, _owner_mismatch
from web.api.candidate_tokens import resolve_token_sid
from web.api.presets_info import _get_locked_preset_info
from web.api.exam_helpers import _calculate_time_remaining, _format_task_data
from web.api.desktop_restore import auto_restore_desktop


def build_session_payload(request):
    # Check query params for admin/candidate mode + candidate token routing
    url_admin = request.query_params.get("admin")
    url_candidate = request.query_params.get("candidate")
    url_preset = request.query_params.get("preset")
    url_token = request.query_params.get("token")  # Per-candidate session token

    admin_auth = is_admin_authenticated(request)
    if url_admin in ("1", "true", "yes") and admin_auth:
        is_admin = True
    else:
        is_admin = False

    cid = _client_id(request)

    # Candidate token routing: resolve session_id from token
    session = None
    if url_token:
        sid_for_token = resolve_token_sid(url_token)
        if sid_for_token:
            state = redis_bus.get_session_state(sid_for_token)
            if state and state.get("status") == "active":
                q_ids = state.get("question_ids", [])
                questions = [loader.get(qid) for qid in q_ids if loader.get(qid) is not None]
                from core.models import ExamSession
                session = ExamSession(
                    session_id=state.get("session_id", "default"),
                    created_at=state.get("created_at", ""),
                    name=state.get("name", "Active Practice Session"),
                    questions=questions,
                    target_contexts=state.get("target_contexts", []),
                    time_limit_minutes=state.get("time_limit_minutes"),
                    mode=state.get("mode", "batch"),
                    current_index=state.get("current_index", 0),
                    scores=state.get("scores", {}),
                    flagged=state.get("flagged", []),
                    scorecard=state.get("scorecard"),
                    status=state.get("status", "active"),
                    last_active_at=state.get("last_active_at"),
                    candidate_token=state.get("candidate_token"),
                    owner_username=state.get("owner_username"),
                    assigned_by=state.get("assigned_by"),
                )

    if session is None:
        # FS-003b: contextual resolution — the authenticated user's own active
        # session (admins may fall back to the legacy most-recent pointer).
        from web.api.session_resolver import resolve_session_id

        sid = resolve_session_id(request, allow_legacy_active=admin_auth)
        if sid:
            session = deployer.load_session(loader, sid)

    # If no active session found but candidate token has an invitation
    if session is None and url_token:
        invitation = redis_bus.get_invitation(url_token)
        if invitation:
            assigned_preset = invitation.get("preset") or redis_bus.get_default_preset()
            preset_info = _get_locked_preset_info(assigned_preset)
            return {
                "active": False,
                "invited": True,
                "preset": assigned_preset,
                "token": url_token,
                "locked_preset": preset_info,
                "is_admin": is_admin,
                "owner_username": None,
                "assigned_by": None,
            }

    preset_info = _get_locked_preset_info(url_preset)

    if not session or getattr(session, "status", "active") != "active":
        return {

            "active": False,
            "session": None,
            "locked_preset": preset_info,
            "is_admin": is_admin,
            "owner_username": None,
            "assigned_by": None,
        }

    # Soft per-session owner lock: a different browser may not attach.
    if _owner_mismatch(session.session_id, cid, admin_auth):
        return {
            "active": False,
            "session": None,
            "locked": True,
            "locked_preset": None,
            "is_admin": is_admin,
            "owner_username": None,
            "assigned_by": None,
        }

    # Auto-Restore Container for Active Sessions
    # Only when the session is genuinely registered as active (not a stale
    # state snapshot from a submitted/terminated session).
    if session and session.session_id and session.status == "active":
        auto_restore_desktop(session.session_id)

    # Touch activity timestamp for idle timeout tracking
    now_utc = datetime.now(timezone.utc)
    try:
        session.last_active_at = now_utc.isoformat()
        deployer.save_session(session)
        redis_bus.touch_session_activity(session.session_id)
    except Exception:
        pass

    cur_idx = session.current_index
    current_q = session.current_question

    task_data = None
    if current_q:
        task_data = _format_task_data(current_q, cur_idx, session)

    time_remaining = _calculate_time_remaining(session)
    start_ts = None
    end_ts = None
    if session.created_at:
        try:
            c_str = session.created_at.replace("Z", "+00:00")
            c_dt = datetime.fromisoformat(c_str)
            if c_dt.tzinfo is None:
                c_dt = c_dt.replace(tzinfo=timezone.utc)
            start_ts = c_dt.timestamp()
            if session.time_limit_minutes:
                end_ts = start_ts + (session.time_limit_minutes * 60)
        except Exception:
            pass

    # Resolve terminal & noVNC URLs
    terminal_port = os.getenv("TERMINAL_PORT", "7681")
    novnc_port = os.getenv("NOVNC_PORT", "6080")

    return {
        "active": True,
        "session_id": session.session_id,
        "candidate_token": session.candidate_token,
        "name": session.name,
        "mode": session.mode,
        "status": session.status,
        "current_index": cur_idx,
        "total_tasks": len(session.questions),
        "time_limit_minutes": session.time_limit_minutes,
        "time_remaining_seconds": time_remaining,
        "created_at": session.created_at,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "server_timestamp": now_utc.timestamp(),
        "flagged_ids": session.flagged,
        "current_task": task_data,
        "terminal_port": terminal_port,
        "novnc_port": novnc_port,
        "is_admin": is_admin,
        "owner_username": session.owner_username,
        "assigned_by": session.assigned_by,
    }
