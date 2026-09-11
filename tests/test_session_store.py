import json
import tempfile
import unittest
from pathlib import Path

from core.deployer import LabDeployer
from core.models import ExamSession
from core.redis_bus import bus
from web.api.session_ownership import record_session_owner, get_user_sessions


class _StubLoader:
    def get(self, qid):
        return None


class _FakeClient:
    def __init__(self):
        self.strings = {}
        self.sets = {}
        self.ttls = {}

    def set(self, key, value, ex=None):
        self.strings[key] = value
        self.ttls[key] = ex

    def sadd(self, key, *values):
        self.sets.setdefault(key, set()).update(values)

    def expire(self, key, ttl):
        self.ttls[key] = ttl

    def smembers(self, key):
        return set(self.sets.get(key, set()))


class _FakeBus:
    def __init__(self):
        self.client = _FakeClient()

    def get_sync_client(self):
        return self.client


class TestSessionStore(unittest.TestCase):
    def setUp(self):
        self._orig_is_available = bus.is_available
        self._orig_mem_states = dict(bus._mem_session_states)
        self._orig_mem_active = bus._mem_active_session_id
        bus.is_available = lambda: False
        bus._mem_session_states = {}
        bus._mem_active_session_id = None

    def tearDown(self):
        bus.is_available = self._orig_is_available
        bus._mem_session_states = self._orig_mem_states
        bus._mem_active_session_id = self._orig_mem_active

    def test_legacy_session_file_migration(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            legacy = tmp_path / "session.json"
            legacy.write_text(json.dumps({
                "session_id": "legacy-123",
                "created_at": "2025-01-01T00:00:00+00:00",
                "name": "Legacy Exam",
                "question_ids": ["TR-001", "CA-001"],
                "target_contexts": ["k3d-cka"],
                "time_limit_minutes": 60,
                "mode": "sequential",
                "current_index": 1,
                "scores": {},
                "flagged": [],
                "status": "active",
                "candidate_token": "tok-legacy",
                "owner_username": "alice",
                "assigned_by": "admin",
            }), encoding="utf-8")

            deployer = LabDeployer(session_file=legacy, sets_dir=tmp_path / "sets")
            session = deployer.load_active_session(_StubLoader())

            self.assertIsNotNone(session)
            self.assertEqual(session.session_id, "legacy-123")
            self.assertEqual(session.name, "Legacy Exam")
            self.assertEqual(session.current_index, 1)
            self.assertEqual(session.owner_username, "alice")
            self.assertEqual(session.assigned_by, "admin")
            self.assertFalse(legacy.exists())
            self.assertTrue((tmp_path / "session.json.migrated").exists())

    def test_round_trip_preserves_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            deployer = LabDeployer(session_file=tmp_path / "session.json", sets_dir=tmp_path / "sets")
            session = ExamSession(
                session_id="s-roundtrip",
                created_at="2025-01-01T00:00:00+00:00",
                name="Round Trip",
                questions=[],
                target_contexts=[],
                owner_username="bob",
                assigned_by="admin",
            )
            deployer.save_session(session)

            state = bus.get_session_state()
            self.assertIsNotNone(state)
            self.assertEqual(state.get("owner_username"), "bob")
            self.assertEqual(state.get("assigned_by"), "admin")

            loaded = deployer.load_active_session(_StubLoader())
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.session_id, "s-roundtrip")
            self.assertEqual(loaded.owner_username, "bob")
            self.assertEqual(loaded.assigned_by, "admin")

    def test_clear_active_session_removes_active_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            deployer = LabDeployer(session_file=tmp_path / "session.json", sets_dir=tmp_path / "sets")
            session = ExamSession(
                session_id="s-clear",
                created_at="2025-01-01T00:00:00+00:00",
                name="Clear Me",
                questions=[],
                target_contexts=[],
            )
            deployer.save_session(session)
            self.assertEqual(bus.get_active_session_id(), "s-clear")

            deployer.clear_active_session()
            self.assertIsNone(bus.get_active_session_id())
            self.assertIsNone(bus.get_session_state())

    def test_record_session_owner_and_index(self):
        fake = _FakeBus()
        record_session_owner("s-1", "alice", "admin", redis_bus=fake)
        record_session_owner("s-2", "alice", redis_bus=fake)

        self.assertEqual(fake.client.strings["session:s-1:owner_user"], "alice")
        self.assertEqual(fake.client.strings["session:s-1:assigned_by"], "admin")
        self.assertNotIn("session:s-2:assigned_by", fake.client.strings)
        self.assertEqual(fake.client.sets["user:alice:sessions"], {"s-1", "s-2"})
        self.assertEqual(get_user_sessions("alice", redis_bus=fake), ["s-1", "s-2"])
        self.assertEqual(get_user_sessions("nobody", redis_bus=fake), [])


if __name__ == "__main__":
    unittest.main()
