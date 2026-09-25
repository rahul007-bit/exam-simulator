"""Admin user-management guards (DELETE /api/admin/users/{username}).

Fastapi/httpx may be unavailable on a dev box, so the endpoint tests skip
cleanly; the handler is exercised directly with a fake user store.
"""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    from fastapi import HTTPException

    import web.api.routes.auth as auth_routes

    HAS_FASTAPI = True
except Exception:  # pragma: no cover - dev box without fastapi
    HAS_FASTAPI = False


@unittest.skipUnless(HAS_FASTAPI, "fastapi unavailable")
class AdminDeleteUserGuardsTest(unittest.TestCase):
    def test_self_delete_is_rejected(self):
        users = SimpleNamespace(
            get_user=lambda u: {"username": "admin", "role": "admin"},
            list_users=lambda: [{"username": "admin", "role": "admin"}],
            delete_user=lambda u: True,
        )
        with patch.object(auth_routes, "users", users), patch.object(
            auth_routes, "resolve_session", lambda request: {"username": "admin"}
        ), patch.object(auth_routes, "require_admin", lambda request: None):
            with self.assertRaises(HTTPException) as ctx:
                auth_routes.admin_delete_user("admin", object())
        self.assertEqual(400, ctx.exception.status_code)

    def test_missing_user_is_404(self):
        users = SimpleNamespace(
            get_user=lambda u: None,
            list_users=lambda: [],
            delete_user=lambda u: False,
        )
        with patch.object(auth_routes, "users", users), patch.object(
            auth_routes, "resolve_session", lambda request: {"username": "bob"}
        ), patch.object(auth_routes, "require_admin", lambda request: None):
            with self.assertRaises(HTTPException) as ctx:
                auth_routes.admin_delete_user("ghost", object())
        self.assertEqual(404, ctx.exception.status_code)

    def test_last_admin_cannot_be_deleted(self):
        users = SimpleNamespace(
            get_user=lambda u: {"username": u, "role": "admin"},
            list_users=lambda: [{"username": "alice", "role": "admin"}],
            delete_user=lambda u: True,
        )
        with patch.object(auth_routes, "users", users), patch.object(
            auth_routes, "resolve_session", lambda request: {"username": "bob"}
        ), patch.object(auth_routes, "require_admin", lambda request: None):
            with self.assertRaises(HTTPException) as ctx:
                auth_routes.admin_delete_user("alice", object())
        self.assertEqual(400, ctx.exception.status_code)

    def test_normal_user_deleted(self):
        deleted = {}
        users = SimpleNamespace(
            get_user=lambda u: {"username": u, "role": "user"},
            list_users=lambda: [{"username": "root", "role": "admin"}],
            delete_user=lambda u: deleted.setdefault("u", u) or True,
        )
        with patch.object(auth_routes, "users", users), patch.object(
            auth_routes, "resolve_session", lambda request: {"username": "root"}
        ), patch.object(auth_routes, "require_admin", lambda request: None):
            result = auth_routes.admin_delete_user("alice", object())
        self.assertEqual({"status": "ok", "username": "alice"}, result)
        self.assertEqual("alice", deleted.get("u"))

    def test_admin_deleted_when_another_admin_remains(self):
        users = SimpleNamespace(
            get_user=lambda u: {"username": u, "role": "admin"},
            list_users=lambda: [
                {"username": "root", "role": "admin"},
                {"username": "alice", "role": "admin"},
            ],
            delete_user=lambda u: True,
        )
        with patch.object(auth_routes, "users", users), patch.object(
            auth_routes, "resolve_session", lambda request: {"username": "root"}
        ), patch.object(auth_routes, "require_admin", lambda request: None):
            result = auth_routes.admin_delete_user("alice", object())
        self.assertEqual({"status": "ok", "username": "alice"}, result)


if __name__ == "__main__":
    unittest.main()
