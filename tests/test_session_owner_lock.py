"""Unit tests for the soft per-session owner lock (web/api/owner_lock.py).

These tests deliberately do NOT import `fastapi` or `web.api.owner_lock` at
module import time: the package pulls in host-only dependencies that are not
available on a Windows dev box. Instead the pure owner-lock helpers are
extracted from the source with `ast` and executed with a fake Redis bus. The
decision logic under test is exactly the code shipped in web/api/owner_lock.py.
"""
import ast
import unittest
from pathlib import Path
from typing import Optional

SERVER = Path(__file__).resolve().parents[1] / "web" / "api" / "owner_lock.py"

_HELPER_NAMES = {
    "_owner_decision",
    "_owner_key",
    "_get_owner",
    "_claim_owner",
    "_clear_owner",
    "_owner_mismatch",
}


class _FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


class _FakeBus:
    def __init__(self):
        self.client = _FakeRedis()

    def get_sync_client(self):
        return self.client


def _extract_helpers():
    source = SERVER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SERVER))
    wanted = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in _HELPER_NAMES]
    found = {n.name for n in wanted}
    missing = _HELPER_NAMES - found
    if missing:
        raise RuntimeError(f"owner-lock helpers missing from web/server.py: {sorted(missing)}")
    return ast.Module(body=wanted, type_ignores=[])


def _load_helpers(bus):
    ns = {
        "Optional": Optional,
        "redis_bus": bus,
        "_CLIENT_ID_COOKIE": "cka_client_id",
        "_OWNER_TTL_SECONDS": 86400,
    }
    exec(compile(_extract_helpers(), str(SERVER), "exec"), ns)
    return ns


class TestOwnerDecision(unittest.TestCase):
    def setUp(self):
        self.bus = _FakeBus()
        self.helpers = _load_helpers(self.bus)
        self.decide = self.helpers["_owner_decision"]

    def test_no_owner_with_client_id_claims(self):
        self.assertEqual(self.decide(None, "client-a", False), "claim")

    def test_matching_owner_allows(self):
        self.assertEqual(self.decide("client-a", "client-a", False), "allow")

    def test_different_owner_rejects(self):
        self.assertEqual(self.decide("client-a", "client-b", False), "reject")

    def test_missing_client_id_allows_without_claim(self):
        self.assertEqual(self.decide(None, None, False), "allow")
        self.assertEqual(self.decide("client-a", None, False), "allow")

    def test_admin_always_allows(self):
        self.assertEqual(self.decide("client-a", "client-b", True), "allow")
        self.assertEqual(self.decide("client-a", None, True), "allow")
        self.assertEqual(self.decide(None, "client-b", True), "allow")


class TestOwnerMismatch(unittest.TestCase):
    def setUp(self):
        self.bus = _FakeBus()
        self.helpers = _load_helpers(self.bus)
        self.mismatch = self.helpers["_owner_mismatch"]
        self.owner_key = self.helpers["_owner_key"]

    def test_claim_on_first_touch_and_allow(self):
        self.assertFalse(self.mismatch("sess-1", "client-a", False))
        self.assertEqual(self.bus.client.store[self.owner_key("sess-1")], "client-a")
        self.assertEqual(self.bus.client.store["session:sess-1:owner"], "client-a")

    def test_same_owner_allows(self):
        self.bus.client.store[self.owner_key("sess-1")] = "client-a"
        self.assertFalse(self.mismatch("sess-1", "client-a", False))
        self.assertEqual(self.bus.client.store[self.owner_key("sess-1")], "client-a")

    def test_other_owner_rejects_without_takeover(self):
        self.bus.client.store[self.owner_key("sess-1")] = "client-a"
        self.assertTrue(self.mismatch("sess-1", "client-b", False))
        self.assertEqual(self.bus.client.store[self.owner_key("sess-1")], "client-a")

    def test_no_client_id_allows_and_does_not_claim(self):
        self.assertFalse(self.mismatch("sess-1", None, False))
        self.assertNotIn(self.owner_key("sess-1"), self.bus.client.store)
        self.bus.client.store[self.owner_key("sess-1")] = "client-a"
        self.assertFalse(self.mismatch("sess-1", None, False))
        self.assertEqual(self.bus.client.store[self.owner_key("sess-1")], "client-a")

    def test_admin_bypasses_and_does_not_take_over(self):
        self.bus.client.store[self.owner_key("sess-1")] = "client-a"
        self.assertFalse(self.mismatch("sess-1", "client-b", True))
        self.assertEqual(self.bus.client.store[self.owner_key("sess-1")], "client-a")

    def test_empty_sid_is_allowed(self):
        self.assertFalse(self.mismatch(None, "client-a", False))


if __name__ == "__main__":
    unittest.main()
