"""FE-040 static cutover regression tests.

Uses only the stdlib at import time: importing fastapi (which transitively needs
``termios``) is deferred to the host-only test so this suite still collects on a
Windows dev box where fastapi may be absent.
"""

import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

EXCLUDE_DIR_NAMES = {
    ".git",
    ".venv",
    "node_modules",
    ".worktrees",
    ".agents",
    "__pycache__",
    "playwright-report",
    "test-results",
}
EXCLUDE_REL_PATHS = {Path("web") / "dist"}
LEGACY_TOKENS = (
    "web/static",
    "static/js",
    "static/css",
    "app.js",
    "admin.js",
    "admin.html",
    "style.css",
)


class FrontendCutoverTest(unittest.TestCase):
    def test_legacy_files_removed(self):
        self.assertFalse(
            (REPO / "web" / "static").exists(),
            "web/static must be deleted (FE-040 cutover)",
        )

    def test_repo_audit_no_legacy_refs(self):
        self_path = Path(__file__).resolve()
        hits = []
        for root, dirs, files in os.walk(REPO):
            root_path = Path(root)
            try:
                rel_root = root_path.relative_to(REPO)
            except ValueError:
                dirs[:] = []
                continue
            dirs[:] = [
                d
                for d in dirs
                if d not in EXCLUDE_DIR_NAMES
                and (rel_root / d) not in EXCLUDE_REL_PATHS
            ]
            for fname in files:
                fp = root_path / fname
                try:
                    if fp.resolve() == self_path:
                        continue
                except OSError:
                    continue
                try:
                    text = fp.read_text(encoding="utf-8")
                except (UnicodeDecodeError, OSError):
                    continue
                for token in LEGACY_TOKENS:
                    if token in text:
                        hits.append(f"{fp.relative_to(REPO)}: {token}")
        self.assertEqual([], hits, "legacy references remain:\n" + "\n".join(hits))

    def test_server_source_cutover(self):
        source = (REPO / "web" / "server.py").read_text(encoding="utf-8")
        self.assertNotIn("STATIC_DIR", source)
        self.assertNotIn("web/static", source)
        self.assertNotIn("admin.html", source)
        self.assertIn("SPA_INDEX", source)
        self.assertIn('@app.get("/admin"', source)

    @unittest.skipIf(os.name == "nt", "host-only (Unix pty/termios)")
    def test_serves_spa_routes_host_only(self):
        try:
            from fastapi.testclient import TestClient
            import web.server as srv
        except ImportError as exc:
            self.skipTest(f"fastapi/httpx unavailable: {exc}")
            return

        client = TestClient(srv.app)
        for route in ("/", "/admin", "/login"):
            resp = client.get(route)
            self.assertEqual(200, resp.status_code, f"{route} -> {resp.status_code}")
            self.assertIn('<div id="app">', resp.text, f"{route} missing SPA mount")
        self.assertEqual(404, client.get("/api/does-not-exist").status_code)


if __name__ == "__main__":
    unittest.main()
