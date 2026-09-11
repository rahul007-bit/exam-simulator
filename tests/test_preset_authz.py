"""Authorization tests for the preset catalog surface (FS-008 / D-010).

Enumeration of presets is admin-only at the API level. These tests assert, at
both source and behavior level, that the `get_presets`, `select_preset` and
`generate_preset` handlers gate on `require_admin` before doing any work, so a
non-admin request receives HTTP 401.
"""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PRESETS_PATH = ROOT / "web" / "api" / "routes" / "presets.py"

GATED_HANDLERS = ("get_presets", "select_preset", "generate_preset")


def _handler_nodes():
    tree = ast.parse(PRESETS_PATH.read_text(encoding="utf-8"))
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in GATED_HANDLERS
    }


def _calls_require_admin(func):
    for node in ast.walk(func):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name) and target.id == "require_admin":
                return True
    return False


class PresetAuthzSourceTest(unittest.TestCase):
    def test_handlers_exist(self):
        handlers = _handler_nodes()
        for name in GATED_HANDLERS:
            with self.subTest(handler=name):
                self.assertIn(name, handlers, f"{name} handler missing from presets.py")

    def test_handlers_call_require_admin(self):
        handlers = _handler_nodes()
        for name in GATED_HANDLERS:
            with self.subTest(handler=name):
                self.assertIn(name, handlers)
                self.assertTrue(
                    _calls_require_admin(handlers[name]),
                    f"{name} does not call require_admin",
                )

    def test_handlers_accept_request(self):
        handlers = _handler_nodes()
        for name in GATED_HANDLERS:
            with self.subTest(handler=name):
                self.assertIn(name, handlers)
                args = [a.arg for a in handlers[name].args.args]
                self.assertIn("request", args, f"{name} lacks a request parameter")


try:
    from fastapi import HTTPException

    from web.api import security as security_module
    from web.api.routes import presets as presets_module
    from web.api.schemas import GeneratePresetRequest, PresetSelectRequest

    _HAS_BEHAVIOR = True
except Exception:
    _HAS_BEHAVIOR = False


class _FakeRequest:
    """Minimal stand-in exposing the attributes security/auth code probes."""

    cookies = {}
    headers = {}
    query_params = {}


@unittest.skipUnless(_HAS_BEHAVIOR, "fastapi/web.api not importable")
class PresetAuthzBehaviorTest(unittest.TestCase):
    def setUp(self):
        self._original = security_module.is_admin_authenticated
        security_module.is_admin_authenticated = lambda req: False
        self.addCleanup(self._restore)

    def _restore(self):
        security_module.is_admin_authenticated = self._original

    def _assert_401(self, call):
        with self.assertRaises(HTTPException) as ctx:
            call()
        self.assertEqual(401, ctx.exception.status_code)

    def test_get_presets_rejects_anonymous(self):
        self._assert_401(lambda: presets_module.get_presets(_FakeRequest()))

    def test_select_preset_rejects_anonymous(self):
        req = PresetSelectRequest(preset="mock-01-acme")
        self._assert_401(lambda: presets_module.select_preset(req, _FakeRequest()))

    def test_generate_preset_rejects_anonymous(self):
        req = GeneratePresetRequest(count=1)
        self._assert_401(lambda: presets_module.generate_preset(req, _FakeRequest()))


if __name__ == "__main__":
    unittest.main()
