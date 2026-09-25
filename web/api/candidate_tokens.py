from typing import Dict, Optional

from core.redis_bus import bus as redis_bus

# In-memory candidate token -> session_id mapping (supplements Redis for fast
# lookup). Redis (token:{tok}) is the source of truth for multi-replica; this
# cache only short-circuits lookups for tokens this process registered.
# token -> session_id
_candidate_token_map: Dict[str, str] = {}


def resolve_token_sid(token: str) -> Optional[str]:
    """Resolves a candidate token to its session_id (cache, then Redis)."""
    sid = _candidate_token_map.get(token)
    if not sid and redis_bus.is_available():
        try:
            val = redis_bus.get_sync_client().get(f"token:{token}")
            if val:
                sid = val if isinstance(val, str) else val.decode()
        except Exception:
            pass
    return sid or None


def register_token(token: str, session_id: str) -> None:
    """Registers token -> session_id in memory and Redis (24h TTL)."""
    _candidate_token_map[token] = session_id
    if redis_bus.is_available():
        try:
            redis_bus.get_sync_client().set(f"token:{token}", session_id, ex=86400)
        except Exception:
            pass
