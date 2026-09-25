"""Unit tests for FS-004 assignment helpers in core.redis_bus.

The helpers are pure dict/Redis operations, so a dict-based fake Redis client is
injected into a `RedisBus` instance; the suite runs on Windows without redis.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from core.redis_bus import RedisBus

    _HAS_REDIS_BUS = True
except Exception:
    _HAS_REDIS_BUS = False


class _FakeRedis:
    """Dict-based stand-in for the sync Redis client (decode_responses=True)."""

    def __init__(self):
        self.strings = {}
        self.sets = {}

    def get(self, key):
        return self.strings.get(key)

    def set(self, key, value, ex=None):
        self.strings[key] = value.decode() if isinstance(value, bytes) else value
        return True

    def delete(self, *keys):
        removed = 0
        for key in keys:
            existed = key in self.strings or key in self.sets
            self.strings.pop(key, None)
            self.sets.pop(key, None)
            removed += 1 if existed else 0
        return removed

    def sadd(self, name, *values):
        members = self.sets.setdefault(name, set())
        added = 0
        for value in values:
            if value not in members:
                members.add(value)
                added += 1
        return added

    def smembers(self, name):
        return set(self.sets.get(name, set()))

    def srem(self, name, *values):
        members = self.sets.get(name, set())
        removed = 0
        for value in values:
            if value in members:
                members.remove(value)
                removed += 1
        return removed

    def ping(self):
        return True


@unittest.skipUnless(_HAS_REDIS_BUS, "core.redis_bus not importable")
class AssignmentHelpersTest(unittest.TestCase):
    def setUp(self):
        self.redis = _FakeRedis()
        self.bus = RedisBus()
        self.bus.is_available = lambda: True
        self.bus.get_sync_client = lambda: self.redis

    def _create(self, token, preset="mock-01-acme", assigned_by="admin", assigned_to=""):
        return self.bus.create_invitation(
            token, preset, assigned_by=assigned_by, assigned_to=assigned_to
        )

    def test_record_carries_assignment_fields(self):
        record = self._create("tok-a", assigned_by="root", assigned_to="alice")
        self.assertEqual(record["assigned_to"], "alice")
        self.assertEqual(record["assigned_by"], "root")
        self.assertEqual(record["status"], "pending")
        stored = json.loads(self.redis.strings["invitation:tok-a"])
        self.assertEqual(stored["assigned_to"], "alice")
        self.assertEqual(stored["assigned_by"], "root")
        self.assertIn("tok-a", self.redis.smembers("candidate_invitations"))

    def test_default_assignment_fields_are_backward_compatible(self):
        record = self._create("tok-plain")
        self.assertEqual(record["assigned_to"], "")
        self.assertEqual(record["assigned_by"], "admin")

    def test_list_assignments_filters_unassigned(self):
        self._create("tok-a", assigned_to="alice")
        self._create("tok-b")
        self._create("tok-c", assigned_to="bob")
        tokens = {inv["token"] for inv in self.bus.list_assignments()}
        self.assertEqual(tokens, {"tok-a", "tok-c"})

    def test_get_user_assignments_filters_by_user(self):
        self._create("tok-a", assigned_to="alice")
        self._create("tok-b", assigned_to="bob")
        self._create("tok-c", assigned_to="alice")
        alice = self.bus.get_user_assignments("alice")
        self.assertEqual({inv["token"] for inv in alice}, {"tok-a", "tok-c"})
        self.assertEqual(self.bus.get_user_assignments("nobody"), [])
        self.assertEqual(self.bus.get_user_assignments(""), [])

    def test_delete_assignment_removes_record_and_membership(self):
        self._create("tok-a", assigned_to="alice")
        self.assertIsNotNone(self.bus.get_invitation("tok-a"))
        self.bus.delete_assignment("tok-a")
        self.assertIsNone(self.bus.get_invitation("tok-a"))
        self.assertNotIn("tok-a", self.redis.smembers("candidate_invitations"))
        self.assertEqual(self.bus.list_assignments(), [])

    def test_helpers_safe_when_redis_unavailable(self):
        self.bus.is_available = lambda: False
        self.assertEqual(self.bus.list_assignments(), [])
        self.assertEqual(self.bus.get_user_assignments("alice"), [])
        self.bus.delete_assignment("tok-a")


if __name__ == "__main__":
    unittest.main()
