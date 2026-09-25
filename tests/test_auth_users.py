"""Unit tests for FS-001 auth backend (web/api/users.py, web/api/auth_sessions.py).

The modules under test are loaded directly from their source files (bypassing
the web.api package __init__, which pulls in fastapi and host-only deps) and
their redis_bus handle is replaced with a dict-based fake, so the suite runs
on a Windows box without fastapi or redis. If fastapi AND httpx ARE available,
an extra endpoint-level suite runs through fastapi.testclient.
"""
import importlib.util
import json
import os
import sys
import time
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import core.redis_bus  # noqa: F401

    _HAS_REDIS_BUS = True
except Exception:
    _HAS_REDIS_BUS = False

if not _HAS_REDIS_BUS:
    _redis_bus_stub = types.ModuleType("core.redis_bus")
    _redis_bus_stub.bus = None
    sys.modules["core.redis_bus"] = _redis_bus_stub


def _load_module(name: str, relpath: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


users_mod = _load_module("fs001_users", "web/api/users.py")
auth_sessions_mod = _load_module("fs001_auth_sessions", "web/api/auth_sessions.py")
security_mod = _load_module("fs001_security", "web/api/security.py")


class _FakeRedis:
    """Dict-based stand-in for the sync Redis client (decode_responses=True)."""

    def __init__(self):
        self.strings = {}
        self.hashes = {}
        self.sets = {}
        self.expiry = {}

    def get(self, key):
        return self.strings.get(key)

    def set(self, key, value, ex=None):
        self.strings[key] = value.decode() if isinstance(value, bytes) else value
        self.expiry[key] = ex
        return True

    def delete(self, *keys):
        removed = 0
        for key in keys:
            existed = key in self.strings or key in self.hashes or key in self.sets
            self.strings.pop(key, None)
            self.hashes.pop(key, None)
            self.sets.pop(key, None)
            self.expiry.pop(key, None)
            removed += 1 if existed else 0
        return removed

    def exists(self, key):
        return 1 if (key in self.strings or key in self.hashes or key in self.sets) else 0

    def hset(self, name, key=None, value=None, mapping=None):
        data = self.hashes.setdefault(name, {})
        if mapping:
            data.update(mapping)
        if key is not None:
            data[key] = value
        return 1

    def hget(self, name, key):
        return self.hashes.get(name, {}).get(key)

    def hgetall(self, name):
        return dict(self.hashes.get(name, {}))

    def sadd(self, name, *values):
        members = self.sets.setdefault(name, set())
        added = 0
        for v in values:
            if v not in members:
                members.add(v)
                added += 1
        return added

    def smembers(self, name):
        return set(self.sets.get(name, set()))

    def srem(self, name, *values):
        members = self.sets.get(name, set())
        removed = 0
        for v in values:
            if v in members:
                members.remove(v)
                removed += 1
        return removed

    def sismember(self, name, value):
        return 1 if value in self.sets.get(name, set()) else 0

    def ping(self):
        return True


class _FakeBus:
    def __init__(self):
        self.client = _FakeRedis()

    def get_sync_client(self):
        return self.client

    def is_available(self):
        return True

    def verify_admin_token(self, token):
        return False

    def store_admin_token(self, token, expires_in=None):
        pass

    def revoke_admin_token(self, token):
        pass


class _FakeRequest:
    def __init__(self, cookies=None, headers=None):
        self.cookies = cookies or {}
        self.headers = headers or {}


_WEB_API_KEYS = (
    "web.api",
    "web.api.users",
    "web.api.auth_sessions",
    "web.api.security",
)


def _install_web_api_stubs():
    """Binds the file-loaded modules as web.api.* so deferred imports resolve."""
    saved = {k: sys.modules.get(k) for k in _WEB_API_KEYS}
    pkg = saved["web.api"]
    created = False
    if pkg is None:
        pkg = types.ModuleType("web.api")
        sys.modules["web.api"] = pkg
        created = True
    sys.modules["web.api.users"] = users_mod
    sys.modules["web.api.auth_sessions"] = auth_sessions_mod
    sys.modules["web.api.security"] = security_mod
    pkg.users = users_mod
    pkg.auth_sessions = auth_sessions_mod
    pkg.security = security_mod

    def _restore():
        if created:
            sys.modules.pop("web.api", None)
        for k, v in saved.items():
            if v is not None:
                sys.modules[k] = v
            else:
                sys.modules.pop(k, None)

    return _restore


try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from pydantic import BaseModel

    _FASTAPI_AVAILABLE = True
except Exception:
    _FASTAPI_AVAILABLE = False


class TestPasswordHashing(unittest.TestCase):
    def test_round_trip(self):
        stored = users_mod.hash_password("s3cret-pw")
        self.assertTrue(stored.startswith("pbkdf2_sha256$390000$"))
        self.assertNotIn("s3cret-pw", stored)
        self.assertTrue(users_mod.verify_password("s3cret-pw", stored))

    def test_unique_salts(self):
        a = users_mod.hash_password("same")
        b = users_mod.hash_password("same")
        self.assertNotEqual(a, b)
        self.assertTrue(users_mod.verify_password("same", a))
        self.assertTrue(users_mod.verify_password("same", b))

    def test_wrong_password(self):
        stored = users_mod.hash_password("correct")
        self.assertFalse(users_mod.verify_password("wrong", stored))

    def test_malformed_hashes(self):
        for bad in ("", "garbage", "pbkdf2_sha256$390000", "pbkdf2_sha256$abc$ab$cd",
                    "md5$390000$ab$cd", "pbkdf2_sha256$390000$zz$cd", None, 123):
            self.assertFalse(users_mod.verify_password("x", bad))


class TestUserStore(unittest.TestCase):
    def setUp(self):
        self.bus = _FakeBus()
        patcher = mock.patch.object(users_mod, "redis_bus", self.bus)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_user_returns_clean_dict(self):
        user = users_mod.create_user("alice", "pw1", "user")
        self.assertEqual(user["username"], "alice")
        self.assertEqual(user["role"], "user")
        self.assertIn("password_hash", user)
        self.assertNotIn("password", user)
        self.assertIn("created_at", user)
        stored = self.bus.client.hgetall("user:alice")
        self.assertTrue(stored["password_hash"].startswith("pbkdf2_sha256$"))

    def test_get_user_round_trip(self):
        users_mod.create_user("bob", "pw2", "admin")
        user = users_mod.get_user("bob")
        self.assertEqual(user["role"], "admin")
        self.assertIn("password_hash", user)
        self.assertIsNone(users_mod.get_user("nobody"))

    def test_duplicate_rejected(self):
        users_mod.create_user("dup", "pw", "user")
        with self.assertRaises(ValueError):
            users_mod.create_user("dup", "other", "user")

    def test_invalid_role_rejected(self):
        with self.assertRaises(ValueError):
            users_mod.create_user("eve", "pw", "root")

    def test_empty_username_and_password_rejected(self):
        with self.assertRaises(ValueError):
            users_mod.create_user("  ", "pw", "user")
        with self.assertRaises(ValueError):
            users_mod.create_user("carol", "", "user")

    def test_list_users_excludes_password_hash(self):
        users_mod.create_user("u1", "pw", "user")
        users_mod.create_user("u2", "pw", "admin")
        listed = users_mod.list_users()
        self.assertEqual([u["username"] for u in listed], ["u1", "u2"])
        for u in listed:
            self.assertNotIn("password_hash", u)
            self.assertIn("role", u)

    def test_delete_user(self):
        users_mod.create_user("gone", "pw", "user")
        self.assertTrue(users_mod.delete_user("gone"))
        self.assertFalse(users_mod.delete_user("gone"))
        self.assertIsNone(users_mod.get_user("gone"))
        self.assertNotIn("gone", self.bus.client.smembers("users"))

    def test_ensure_bootstrap_admin_idempotent(self):
        env = {"AUTH_ADMIN_USER": "testadmin", "AUTH_ADMIN_PASSWORD": "secret123"}
        with mock.patch.dict(os.environ, env, clear=False):
            users_mod.ensure_bootstrap_admin()
            users_mod.ensure_bootstrap_admin()
        users_list = users_mod.list_users()
        self.assertEqual(len(users_list), 1)
        self.assertEqual(users_list[0]["username"], "testadmin")
        self.assertEqual(users_list[0]["role"], "admin")
        self.assertTrue(users_mod.verify_password("secret123", users_mod.get_user("testadmin")["password_hash"]))

    def test_ensure_bootstrap_admin_skips_when_users_exist(self):
        users_mod.create_user("existing", "pw", "user")
        env = {"AUTH_ADMIN_USER": "boot", "AUTH_ADMIN_PASSWORD": "bootpw"}
        with mock.patch.dict(os.environ, env, clear=False):
            users_mod.ensure_bootstrap_admin()
        self.assertIsNone(users_mod.get_user("boot"))
        self.assertEqual(len(users_mod.list_users()), 1)


class TestAuthSessions(unittest.TestCase):
    def setUp(self):
        self.bus = _FakeBus()
        patcher = mock.patch.object(auth_sessions_mod, "redis_bus", self.bus)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_and_resolve_via_cookie(self):
        token = auth_sessions_mod.create_session("alice", "admin")
        req = _FakeRequest(cookies={auth_sessions_mod.AUTH_COOKIE: token})
        session = auth_sessions_mod.resolve_session(req)
        self.assertEqual(session["username"], "alice")
        self.assertEqual(session["role"], "admin")
        self.assertEqual(session["token"], token)
        key = f"auth:session:{token}"
        self.assertIn(key, self.bus.client.strings)
        payload = json.loads(self.bus.client.strings[key])
        self.assertEqual(payload["username"], "alice")
        self.assertIn("created_at", payload)
        self.assertEqual(self.bus.client.expiry[key], 604800)

    def test_resolve_via_bearer(self):
        token = auth_sessions_mod.create_session("bob", "user")
        req = _FakeRequest(headers={"Authorization": f"Bearer {token}"})
        session = auth_sessions_mod.resolve_session(req)
        self.assertEqual(session["username"], "bob")

    def test_cookie_preferred_over_bearer(self):
        t1 = auth_sessions_mod.create_session("a", "user")
        t2 = auth_sessions_mod.create_session("b", "user")
        req = _FakeRequest(
            cookies={auth_sessions_mod.AUTH_COOKIE: t1},
            headers={"Authorization": f"Bearer {t2}"},
        )
        self.assertEqual(auth_sessions_mod.resolve_session(req)["username"], "a")

    def test_unknown_token_resolves_none(self):
        req = _FakeRequest(cookies={auth_sessions_mod.AUTH_COOKIE: "no-such-token"})
        self.assertIsNone(auth_sessions_mod.resolve_session(req))
        req = _FakeRequest(headers={"Authorization": "Bearer nope"})
        self.assertIsNone(auth_sessions_mod.resolve_session(req))
        self.assertIsNone(auth_sessions_mod.resolve_session(_FakeRequest()))

    def test_destroy_session(self):
        token = auth_sessions_mod.create_session("carol", "user")
        req = _FakeRequest(cookies={auth_sessions_mod.AUTH_COOKIE: token})
        auth_sessions_mod.destroy_session(req)
        self.assertIsNone(auth_sessions_mod.resolve_session(req))
        auth_sessions_mod.destroy_session(req)

    def test_destroy_session_removes_bearer_variant_too(self):
        t_cookie = auth_sessions_mod.create_session("d", "user")
        t_bearer = auth_sessions_mod.create_session("e", "user")
        req = _FakeRequest(
            cookies={auth_sessions_mod.AUTH_COOKIE: t_cookie},
            headers={"Authorization": f"Bearer {t_bearer}"},
        )
        auth_sessions_mod.destroy_session(req)
        self.assertNotIn(f"auth:session:{t_cookie}", self.bus.client.strings)
        self.assertNotIn(f"auth:session:{t_bearer}", self.bus.client.strings)


class TestSecurityAdminSession(unittest.TestCase):
    def setUp(self):
        self.bus = _FakeBus()
        restore = _install_web_api_stubs()
        self.addCleanup(restore)
        for target, attr, value in (
            (security_mod, "redis_bus", self.bus),
            (security_mod, "_admin_tokens", set()),
            (auth_sessions_mod, "redis_bus", self.bus),
        ):
            patcher = mock.patch.object(target, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_admin_session_grants_admin(self):
        token = auth_sessions_mod.create_session("root", "admin")
        req = _FakeRequest(cookies={auth_sessions_mod.AUTH_COOKIE: token})
        self.assertTrue(security_mod.is_admin_authenticated(req))
        req = _FakeRequest(headers={"Authorization": f"Bearer {token}"})
        self.assertTrue(security_mod.is_admin_authenticated(req))

    def test_user_session_does_not_grant_admin(self):
        token = auth_sessions_mod.create_session("pleb", "user")
        req = _FakeRequest(cookies={auth_sessions_mod.AUTH_COOKIE: token})
        self.assertFalse(security_mod.is_admin_authenticated(req))

    def test_no_session(self):
        self.assertFalse(security_mod.is_admin_authenticated(_FakeRequest()))

    def test_stale_session_does_not_grant_admin(self):
        token = auth_sessions_mod.create_session("gone", "admin")
        self.bus.client.strings.pop(f"auth:session:{token}")
        req = _FakeRequest(cookies={auth_sessions_mod.AUTH_COOKIE: token})
        self.assertFalse(security_mod.is_admin_authenticated(req))


def _build_endpoint_client(bus):
    restore = _install_web_api_stubs()
    saved_schemas = sys.modules.get("web.api.schemas")
    schemas_mod = types.ModuleType("web.api.schemas")

    class LoginRequest(BaseModel):
        username: str
        password: str

    class CreateUserRequest(BaseModel):
        username: str
        password: str
        role: str = "user"

    schemas_mod.LoginRequest = LoginRequest
    schemas_mod.CreateUserRequest = CreateUserRequest
    sys.modules["web.api.schemas"] = schemas_mod

    routes_mod = _load_module("fs001_routes_auth", "web/api/routes/auth.py")
    users_mod.redis_bus = bus
    auth_sessions_mod.redis_bus = bus
    security_mod.redis_bus = bus
    security_mod._admin_tokens = set()

    def _restore_all():
        if saved_schemas is None:
            sys.modules.pop("web.api.schemas", None)
        else:
            sys.modules["web.api.schemas"] = saved_schemas
        restore()

    app = FastAPI()
    app.include_router(routes_mod.router)
    return TestClient(app), _restore_all


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi/httpx not available")
class TestAuthEndpoints(unittest.TestCase):
    def setUp(self):
        self.bus = _FakeBus()
        self.client, restore = _build_endpoint_client(self.bus)
        self.addCleanup(restore)

    def test_login_me_logout_flow(self):
        users_mod.create_user("alice", "pw", "user")
        r = self.client.post("/api/auth/login", json={"username": "alice", "password": "pw"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok", "username": "alice", "role": "user"})
        self.assertIn(auth_sessions_mod.AUTH_COOKIE, r.cookies)

        r = self.client.get("/api/auth/me")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"username": "alice", "role": "user", "authenticated": True})

        r = self.client.post("/api/auth/logout")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok", "authenticated": False})
        r = self.client.get("/api/auth/me")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json(), {"authenticated": False})

    def test_login_invalid_credentials(self):
        users_mod.create_user("bob", "pw", "user")
        r = self.client.post("/api/auth/login", json={"username": "bob", "password": "wrong"})
        self.assertEqual(r.status_code, 401)
        r = self.client.post("/api/auth/login", json={"username": "ghost", "password": "x"})
        self.assertEqual(r.status_code, 401)

    def test_me_unauthenticated(self):
        r = self.client.get("/api/auth/me")
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json(), {"authenticated": False})

    def test_admin_user_management(self):
        users_mod.create_user("root", "rootpw", "admin")
        token = auth_sessions_mod.create_session("root", "admin")
        headers = {"Authorization": f"Bearer {token}"}
        r = self.client.post(
            "/api/admin/users",
            json={"username": "newbie", "password": "pw", "role": "user"},
            headers=headers,
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["user"]["username"], "newbie")
        self.assertNotIn("password_hash", r.json()["user"])

        r = self.client.get("/api/admin/users", headers=headers)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["total"], 2)
        for u in body["users"]:
            self.assertNotIn("password_hash", u)

    def test_admin_endpoints_reject_non_admin(self):
        users_mod.create_user("pleb", "pw", "user")
        token = auth_sessions_mod.create_session("pleb", "user")
        headers = {"Authorization": f"Bearer {token}"}
        r = self.client.get("/api/admin/users", headers=headers)
        self.assertEqual(r.status_code, 401)
        r = self.client.post(
            "/api/admin/users",
            json={"username": "x", "password": "y", "role": "user"},
            headers=headers,
        )
        self.assertEqual(r.status_code, 401)

    def test_admin_duplicate_user_is_400(self):
        users_mod.create_user("root", "rootpw", "admin")
        token = auth_sessions_mod.create_session("root", "admin")
        headers = {"Authorization": f"Bearer {token}"}
        r = self.client.post(
            "/api/admin/users",
            json={"username": "root", "password": "pw2", "role": "user"},
            headers=headers,
        )
        self.assertEqual(r.status_code, 400)


if __name__ == "__main__":
    unittest.main()
