from typing import Optional

from fastapi import HTTPException, Request

from core.redis_bus import bus as redis_bus
from web.api.security import is_admin_authenticated

_CLIENT_ID_COOKIE = "cka_client_id"
_OWNER_TTL_SECONDS = 86400


def _owner_decision(owner, cid, is_admin):
    """Pure decision for the soft per-session owner lock.

    Returns 'allow', 'claim' or 'reject'. Deliberately free of Redis/FastAPI
    access so it can be unit-tested directly.
    """
    if is_admin:
        return "allow"
    if cid is None:
        # Internal tooling (scripts, curl, background jobs) carries no cookie:
        # keep today's behaviour (never reject, never claim).
        return "allow"
    if owner is None:
        return "claim"
    if owner == cid:
        return "allow"
    return "reject"


def _client_id(request) -> Optional[str]:
    try:
        val = request.cookies.get(_CLIENT_ID_COOKIE)
    except Exception:
        return None
    return val or None


def _client_id_ws(websocket) -> Optional[str]:
    try:
        val = websocket.cookies.get(_CLIENT_ID_COOKIE)
    except Exception:
        return None
    return val or None


def _owner_key(sid: str) -> str:
    return f"session:{sid}:owner"


def _get_owner(sid: Optional[str]) -> Optional[str]:
    if not sid:
        return None
    try:
        val = redis_bus.get_sync_client().get(_owner_key(sid))
    except Exception:
        return None
    if isinstance(val, bytes):
        val = val.decode()
    return val or None


def _claim_owner(sid: Optional[str], cid: Optional[str]) -> None:
    if not sid or not cid:
        return
    try:
        redis_bus.get_sync_client().set(_owner_key(sid), cid, ex=_OWNER_TTL_SECONDS)
    except Exception:
        pass


def _clear_owner(sid: Optional[str]) -> None:
    if not sid:
        return
    try:
        redis_bus.get_sync_client().delete(_owner_key(sid))
    except Exception:
        pass


def _owner_mismatch(sid: Optional[str], cid: Optional[str], is_admin: bool) -> bool:
    """True when a different client owns the session; claims on first touch."""
    if not sid:
        return False
    decision = _owner_decision(_get_owner(sid), cid, is_admin)
    if decision == "claim":
        _claim_owner(sid, cid)
        return False
    return decision == "reject"


def _enforce_owner(request: Request, sid: Optional[str]) -> None:
    """Raise 409 when the caller is not the owner of the active session."""
    if sid and _owner_mismatch(sid, _client_id(request), is_admin_authenticated(request)):
        raise HTTPException(status_code=409, detail="This exam session is active in another window or device.")
