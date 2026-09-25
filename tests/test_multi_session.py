"""FS-003b — concurrent per-user session registry (core.redis_bus).

Uses a RedisBus pointed at an unreachable port so `is_available()` is False and
the in-memory fallback path is exercised; no Redis server is required.
"""
import unittest

from core.redis_bus import RedisBus


def _bus():
    bus = RedisBus()
    # Force the in-memory fallback path without any network probe (a real
    # unreachable host makes redis-py retry and can hang the suite).
    bus.is_available = lambda: False  # type: ignore[method-assign]
    return bus


class MultiSessionRegistryTest(unittest.TestCase):
    def setUp(self):
        self.bus = _bus()

    def test_multiple_sessions_are_registered_and_listed(self):
        self.assertFalse(self.bus.is_available())

        self.bus.set_session_state("s1", {"session_id": "s1", "status": "active"})
        self.bus.set_session_state("s2", {"session_id": "s2", "status": "active"})

        self.assertTrue(self.bus.is_session_active("s1"))
        self.assertTrue(self.bus.is_session_active("s2"))
        self.assertEqual({"s1", "s2"}, set(self.bus.list_active_session_ids()))

    def test_clearing_one_session_leaves_the_other(self):
        self.bus.set_session_state("s1", {"session_id": "s1"})
        self.bus.set_session_state("s2", {"session_id": "s2"})

        self.bus.clear_session_state("s1")

        self.assertFalse(self.bus.is_session_active("s1"))
        self.assertTrue(self.bus.is_session_active("s2"))
        self.assertEqual(["s2"], self.bus.list_active_session_ids())

    def test_user_active_session_index(self):
        self.bus.set_session_state("sA", {"session_id": "sA"})
        self.bus.set_session_state("sB", {"session_id": "sB"})

        self.bus.set_user_active_session("alice", "sA")
        self.bus.set_user_active_session("bob", "sB")

        self.assertEqual("sA", self.bus.get_user_active_session("alice"))
        self.assertEqual("sB", self.bus.get_user_active_session("bob"))

        self.bus.clear_user_active_session("alice")
        self.assertIsNone(self.bus.get_user_active_session("alice"))
        self.assertEqual("sB", self.bus.get_user_active_session("bob"))

    def test_legacy_pointer_tracks_most_recent(self):
        self.bus.set_session_state("s1", {"session_id": "s1"})
        self.bus.set_session_state("s2", {"session_id": "s2"})

        self.assertEqual("s2", self.bus.get_active_session_id())

    def test_unknown_session_is_not_active(self):
        self.assertFalse(self.bus.is_session_active("nope"))
        self.assertIsNone(self.bus.get_user_active_session("nobody"))


if __name__ == "__main__":
    unittest.main()
