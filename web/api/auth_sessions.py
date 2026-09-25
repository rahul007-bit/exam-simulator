import json
import secrets
from datetime import datetime, timezone
from typing import Optional

from core.redis_bus import bus as redis_bus

AUTH_COOKIE = "cka_auth_token"
SESSION_TTL_SECONDS = 604800


def _client():
    client = redis_bus.get_sync_client()
    if client is None:
        raise RuntimeError("Redis unavailable: redis_bus returned no client")
    return client


def _session_key(token: str) -> str:
    return f"auth:session:{token}"


def _bearer_token(request) -> Optional[str]:
    try:
        auth_header = request.headers.get("authorization", "") or request.headers.get("Authorization", "")
    except Exception:
        return None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        return token or None
    return None


def create_session(username: str, role: str) -> str:
    """Stores a login session in Redis with a 7-day TTL and returns the token."""
    token = secrets.token_urlsafe(32)
    payload = json.dumps(
        {
            "username": username,
            "role": role,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _client().set(_session_key(token), payload, ex=SESSION_TTL_SECONDS)
    return token


def resolve_session(request) -> Optional[dict]:
    """Resolves the auth session from the cookie, falling back to Bearer."""
    token = None
    try:
        token = request.cookies.get(AUTH_COOKIE)
    except Exception:
        token = None
    if not token:
        token = _bearer_token(request)
    if not token:
        return None
    try:
        raw = _client().get(_session_key(token))
    except Exception:
        return None
    if not raw:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return {"username": data.get("username"), "role": data.get("role"), "token": token}


def destroy_session(request) -> None:
    """Deletes the Redis session key(s) referenced by cookie and/or Bearer."""
    tokens = []
    try:
        cookie_token = request.cookies.get(AUTH_COOKIE)
        if cookie_token:
            tokens.append(cookie_token)
    except Exception:
        pass
    bearer_token = _bearer_token(request)
    if bearer_token and bearer_token not in tokens:
        tokens.append(bearer_token)
    if not tokens:
        return
    try:
        _client().delete(*[_session_key(t) for t in tokens])
    except Exception:
        pass
