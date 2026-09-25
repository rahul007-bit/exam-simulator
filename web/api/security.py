import os

from core.redis_bus import bus as redis_bus

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# In-process fast-path cache of issued admin tokens. The authoritative store is
# Redis (store_admin_token / verify_admin_token); this cache only short-circuits
# lookups for tokens this process issued and is safe to lose (multi-replica OK).
_admin_tokens: set = set()


def is_admin_authenticated(req_or_ws) -> bool:
    """Checks if request or websocket carries valid admin credentials."""
    # 1. Cookie check
    cookie_token = None
    if hasattr(req_or_ws, "cookies") and req_or_ws.cookies:
        cookie_token = req_or_ws.cookies.get("admin_token")
    if cookie_token:
        if cookie_token in _admin_tokens or redis_bus.verify_admin_token(cookie_token):
            return True

    # 2. Authorization Bearer header
    headers = getattr(req_or_ws, "headers", {}) or {}
    auth_header = headers.get("authorization", "") or headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token in _admin_tokens or redis_bus.verify_admin_token(token):
            return True

    # 3. Query param check (e.g. for WebSockets or iframes)
    params = getattr(req_or_ws, "query_params", {}) or {}
    q_token = params.get("admin_token")
    if q_token:
        if q_token in _admin_tokens or redis_bus.verify_admin_token(q_token):
            return True

    # 4. FS-001 user auth session (must carry the admin role)
    from web.api import auth_sessions

    session = auth_sessions.resolve_session(req_or_ws)
    if session and session.get("role") == "admin":
        return True

    # 5. Fallback to EXAM_ADMIN env
    if os.getenv("EXAM_ADMIN", "0").lower() in ("1", "true"):
        return True

    return False


def require_admin(request) -> None:
    """Raises HTTP 401 when the request is not an authenticated admin."""
    from fastapi import HTTPException

    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_user(request) -> None:
    """Raises HTTP 401 unless the request has an admin or a user session."""
    from fastapi import HTTPException

    if is_admin_authenticated(request):
        return
    from web.api import auth_sessions

    if auth_sessions.resolve_session(request):
        return
    raise HTTPException(status_code=401, detail="Unauthorized")


def issue_admin_token() -> str:
    """Creates a new admin token, caches it locally and stores it in Redis."""
    import secrets

    token = secrets.token_urlsafe(32)
    _admin_tokens.add(token)
    redis_bus.store_admin_token(token, expires_in=86400 * 7)
    return token


def revoke_admin_token(token: str) -> None:
    """Removes an admin token from the local cache and Redis."""
    _admin_tokens.discard(token)
    redis_bus.revoke_admin_token(token)
