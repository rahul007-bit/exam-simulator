"""Route-inventory regression test (backend modularization).

The web/server.py -> web/api split is a code move; every route that existed
before must stay registered. This test parses the route module sources (stdlib
only, so it runs on Windows without fastapi) and asserts the full HTTP +
WebSocket surface is present. It exists because a refactor once dropped
POST /api/action/submit, which silently fell through to the SPA catch-all.
"""
import re
import unittest
from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[1] / "web" / "api" / "routes"

_DECORATOR = re.compile(r'@router\.(get|post|put|delete|patch|websocket)\(\s*"([^"]+)"')

EXPECTED = {
    ("get", "/api/session"),
    ("get", "/api/questions"),
    ("get", "/api/timer"),
    ("get", "/api/sessions"),
    ("get", "/api/presets"),
    ("post", "/api/presets/select"),
    ("post", "/api/presets/generate"),
    ("get", "/api/clipboard"),
    ("post", "/api/clipboard"),
    ("get", "/api/reports"),
    ("get", "/api/reports/{filename}"),
    ("get", "/api/recordings"),
    ("get", "/api/recordings/{session_id}"),
    ("get", "/api/recordings/{session_id}/cast"),
    ("get", "/api/recordings/{session_id}/events"),
    ("post", "/api/recordings/{session_id}/event"),
    ("post", "/api/start"),
    ("post", "/api/reset"),
    ("post", "/api/end"),
    ("post", "/api/session/restore"),
    ("post", "/api/action/next"),
    ("post", "/api/action/prev"),
    ("post", "/api/action/jump"),
    ("post", "/api/action/flag"),
    ("post", "/api/action/retry"),
    ("post", "/api/action/submit"),
    ("post", "/api/auth/login"),
    ("post", "/api/auth/logout"),
    ("get", "/api/auth/me"),
    ("post", "/api/admin/users"),
    ("get", "/api/admin/users"),
    ("delete", "/api/admin/users/{username}"),
    ("post", "/api/admin/login"),
    ("get", "/api/admin/check"),
    ("post", "/api/admin/logout"),
    ("get", "/api/admin/config"),
    ("post", "/api/admin/config"),
    ("get", "/api/admin/resources"),
    ("post", "/api/admin/resources"),
    ("post", "/api/admin/sessions/create"),
    ("get", "/api/admin/sessions"),
    ("get", "/api/admin/session/{session_id}"),
    ("post", "/api/admin/sessions/{identifier}/terminate"),
    ("post", "/api/admin/sessions/{identifier}/reset"),
    ("post", "/api/admin/sessions/{identifier}/end"),
    ("get", "/api/admin/infrastructure"),
    ("post", "/api/admin/infrastructure/terminate"),
    ("get", "/admin"),
    ("get", "/{full_path:path}"),
    ("websocket", "/ws/terminal"),
    ("websocket", "/ws/terminal/{session_id}"),
    ("websocket", "/ws/desktop/{session_id}"),
    ("websocket", "/novnc/ws/desktop/{session_id}"),
    ("websocket", "/ws/desktop"),
    ("websocket", "/novnc/ws/desktop"),
    ("websocket", "/ws/vnc"),
    ("websocket", "/websockify"),
    ("websocket", "/novnc/websockify"),
    ("websocket", "/novnc/ws/vnc"),
    ("websocket", "/ws/session/{session_id}"),
}


def _registered():
    registered = set()
    for path in sorted(ROUTES_DIR.glob("*.py")):
        for method, route in _DECORATOR.findall(path.read_text(encoding="utf-8")):
            registered.add((method, route))
    return registered


class RouteInventoryTest(unittest.TestCase):
    def test_all_expected_routes_registered(self):
        registered = _registered()
        missing = sorted(EXPECTED - registered)
        self.assertEqual([], missing, f"routes missing from web/api/routes: {missing}")


if __name__ == "__main__":
    unittest.main()
