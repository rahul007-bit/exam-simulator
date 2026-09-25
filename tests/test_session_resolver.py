"""Session resolver ownership gate (FS-003b fix).

`/api/session` must not return another user's session via the legacy
most-recent pointer. Fastapi may be absent on a dev box, so the module import
is guarded and the tests skip cleanly.
"""
import unittest
from unittest.mock import patch

try:
    import web.api.session_resolver as resolver

    HAS_RESOLVER = True
except Exception:  # pragma: no cover - dev box without fastapi
    HAS_RESOLVER = False


class _FakeRequest:
    def __init__(self, query=None):
        self.query_params = query or {}


@unittest.skipUnless(HAS_RESOLVER, "web.api.session_resolver unavailable")
class ResolverOwnershipTest(unittest.TestCase):
    def _resolve(self, *, user, token_sid, active_sid, state):
        with patch.object(resolver, "resolve_session", lambda request: user), patch.object(
            resolver, "resolve_token_sid", lambda token: token_sid
        ), patch.object(
            resolver.redis_bus, "get_active_session_id", lambda: active_sid
        ), patch.object(
            resolver.redis_bus, "get_session_state", lambda sid=None: state
        ), patch.object(
            resolver.redis_bus, "get_user_active_session", lambda username: None
        ):
            return resolver.resolve_session_id(_FakeRequest(), allow_legacy_active=True)

    def test_legacy_pointer_never_returns_another_users_session(self):
        result = self._resolve(
            user=None,
            token_sid=None,
            active_sid="s-rahul",
            state={"owner_username": "rahul"},
        )
        self.assertIsNone(result)

    def test_legacy_pointer_returns_unowned_session(self):
        result = self._resolve(
            user=None,
            token_sid=None,
            active_sid="s-tool",
            state={},
        )
        self.assertEqual("s-tool", result)

    def test_legacy_pointer_returns_own_session(self):
        result = self._resolve(
            user={"username": "rahul"},
            token_sid=None,
            active_sid="s-rahul",
            state={"owner_username": "rahul"},
        )
        self.assertEqual("s-rahul", result)

    def test_token_resolution_wins(self):
        with patch.object(resolver, "resolve_token_sid", lambda token: "s-token"), patch.object(
            resolver, "resolve_session", lambda request: None
        ), patch.object(resolver.redis_bus, "get_user_active_session", lambda u: None):
            self.assertEqual(
                "s-token",
                resolver.resolve_session_id(_FakeRequest({"token": "abc"}), allow_legacy_active=True),
            )


if __name__ == "__main__":
    unittest.main()
