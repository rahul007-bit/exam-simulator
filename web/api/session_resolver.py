from typing import Optional

from core.models import ExamSession
from core.redis_bus import bus as redis_bus

from web.api.auth_sessions import resolve_session
from web.api.candidate_tokens import resolve_token_sid
from web.api.state import deployer, loader


def resolve_session_id(request, allow_legacy_active: bool = False) -> Optional[str]:
    """Resolves the session a request is about (FS-003b, contextual).

    Order: explicit candidate token -> the authenticated user's active session
    -> (optionally) the legacy most-recent pointer for tools/admins. A candidate
    never falls back to "whatever session is globally active".
    """
    params = getattr(request, "query_params", None) or {}
    token = params.get("token")
    if token:
        sid = resolve_token_sid(token)
        if sid:
            return sid

    user = resolve_session(request)
    if user and user.get("username"):
        sid = redis_bus.get_user_active_session(user["username"])
        if sid:
            return sid

    if allow_legacy_active:
        # Legacy most-recent pointer. In a multi-session world it must never
        # hand back another user's session — only an unowned (tool/default)
        # session, or one the caller actually owns.
        sid = redis_bus.get_active_session_id()
        if sid:
            state = redis_bus.get_session_state(sid) or {}
            owner = state.get("owner_username")
            caller = user.get("username") if user else None
            if not owner or (caller and owner == caller):
                return sid
        return None
    return None


def load_request_session(request, allow_legacy_active: bool = False) -> Optional[ExamSession]:
    sid = resolve_session_id(request, allow_legacy_active=allow_legacy_active)
    if not sid:
        return None
    return deployer.load_session(loader, sid)
