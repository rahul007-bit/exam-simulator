import hashlib
import hmac
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from core.redis_bus import bus as redis_bus

VALID_ROLES = ("admin", "user")
PBKDF2_ITERATIONS = 390000

_USERS_SET_KEY = "users"


def _client():
    client = redis_bus.get_sync_client()
    if client is None:
        raise RuntimeError("Redis unavailable: redis_bus returned no client")
    return client


def _user_key(username: str) -> str:
    return f"user:{username}"


def _decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value


def hash_password(password: str) -> str:
    """Hashes a password with PBKDF2-SHA256 and a random 16-byte salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Constant-time password verification; malformed hashes verify False."""
    if not stored_hash or not isinstance(stored_hash, str):
        return False
    try:
        algo, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def create_user(username: str, password: str, role: str = "user") -> dict:
    """Creates a user in Redis; only the PBKDF2 hash is ever stored."""
    if not isinstance(username, str) or not username.strip():
        raise ValueError("Username must be a non-empty string")
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string")
    if role not in VALID_ROLES:
        raise ValueError(f"Role must be one of {list(VALID_ROLES)}")
    username = username.strip()
    client = _client()
    if client.hgetall(_user_key(username)):
        raise ValueError(f"User '{username}' already exists")
    user = {
        "username": username,
        "role": role,
        "password_hash": hash_password(password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    client.hset(_user_key(username), mapping=user)
    client.sadd(_USERS_SET_KEY, username)
    return dict(user)


def get_user(username: str) -> Optional[dict]:
    """Returns the full user record (including password_hash) or None."""
    if not username:
        return None
    data = _client().hgetall(_user_key(username))
    if not data:
        return None
    return {_decode(k): _decode(v) for k, v in data.items()}


def list_users() -> list:
    """Returns all users without their password hashes."""
    client = _client()
    usernames = sorted(_decode(m) for m in (client.smembers(_USERS_SET_KEY) or set()))
    result = []
    for name in usernames:
        user = get_user(name)
        if user:
            result.append({k: v for k, v in user.items() if k != "password_hash"})
    return result


def delete_user(username: str) -> bool:
    """Deletes a user; returns True if the user existed."""
    if not username:
        return False
    client = _client()
    if not client.hgetall(_user_key(username)):
        return False
    client.delete(_user_key(username))
    client.srem(_USERS_SET_KEY, username)
    return True


def ensure_bootstrap_admin() -> None:
    """Creates the bootstrap admin when no users exist at all; idempotent."""
    if list_users():
        return
    username = os.getenv("AUTH_ADMIN_USER", "admin")
    password = os.getenv("AUTH_ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD") or "admin123"
    create_user(username, password, "admin")
