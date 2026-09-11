from typing import List, Optional

from core.redis_bus import bus as _default_bus

_OWNER_TTL_SECONDS = 86400
_SESSIONS_TTL_SECONDS = 604800


def record_session_owner(
    session_id: str,
    owner_username: Optional[str],
    assigned_by: Optional[str] = None,
    redis_bus=None,
) -> None:
    """Records the owning user (and assigner) for a session plus a per-user index."""
    if not session_id or not owner_username:
        return
    bus = redis_bus or _default_bus
    try:
        client = bus.get_sync_client()
        if client is None:
            return
        client.set(f"session:{session_id}:owner_user", owner_username, ex=_OWNER_TTL_SECONDS)
        if assigned_by:
            client.set(f"session:{session_id}:assigned_by", assigned_by, ex=_OWNER_TTL_SECONDS)
        sessions_key = f"user:{owner_username}:sessions"
        client.sadd(sessions_key, session_id)
        client.expire(sessions_key, _SESSIONS_TTL_SECONDS)
    except Exception:
        pass


def get_user_sessions(owner_username: Optional[str], redis_bus=None) -> List[str]:
    """Returns the sorted session ids owned by a user (empty on error)."""
    if not owner_username:
        return []
    bus = redis_bus or _default_bus
    try:
        client = bus.get_sync_client()
        if client is None:
            return []
        members = client.smembers(f"user:{owner_username}:sessions") or set()
        return sorted(m if isinstance(m, str) else m.decode() for m in members)
    except Exception:
        return []
