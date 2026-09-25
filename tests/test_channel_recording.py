import json
import tempfile
import unittest
from pathlib import Path

from core.recorder import SessionRecorder


class TestChannelRecording(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.recordings_path = Path(self.temp_dir.name)
        self.recorder = SessionRecorder(recordings_dir=self.recordings_path)

    def tearDown(self):
        self.recorder.close()
        self.temp_dir.cleanup()

    def _read_header(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.loads(f.readline())

    def test_two_channels_produce_separate_casts(self):
        session_id = "chan-two"
        self.recorder.start_session(session_id, name="Channel Test")
        self.recorder.record_output("user output\n", channel="user-web")
        self.recorder.record_output("admin output\n", channel="admin-web")
        self.recorder.close()

        user_cast = self.recordings_path / f"{session_id}.user-web.cast"
        admin_cast = self.recordings_path / f"{session_id}.admin-web.cast"

        self.assertTrue(user_cast.exists())
        self.assertTrue(admin_cast.exists())

        for cast in (user_cast, admin_cast):
            header = self._read_header(cast)
            self.assertEqual(header["version"], 2)
            self.assertEqual(header["width"], 120)
            self.assertEqual(header["height"], 34)

        user_body = user_cast.read_text(encoding="utf-8")
        admin_body = admin_cast.read_text(encoding="utf-8")
        self.assertIn("user output", user_body)
        self.assertNotIn("admin output", user_body)
        self.assertIn("admin output", admin_body)
        self.assertNotIn("user output", admin_body)

    def test_admin_input_event_carries_channel_and_actor(self):
        session_id = "chan-admin"
        self.recorder.start_session(session_id, name="Admin Channel Test")
        self.recorder.record_input("kubectl get nodes\r", actor="admin", channel="admin-web")
        self.recorder.flush_input_buffer("admin")

        admin_cast = self.recordings_path / f"{session_id}.admin-web.cast"
        self.assertTrue(admin_cast.exists())
        with open(admin_cast, "r", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(lines[0]["version"], 2)
        inputs = [item[2] for item in lines[1:] if item[1] == "i"]
        self.assertIn("kubectl get nodes\r", inputs)

        events = self.recorder.get_events(session_id)
        admin_events = [e for e in events if e["event"] == "ADMIN_TERMINAL_INPUT"]
        self.assertTrue(admin_events)
        self.assertEqual(admin_events[0]["channel"], "admin-web")
        self.assertEqual(admin_events[0]["actor"], "admin")

    def test_get_cast_path_falls_back_to_legacy(self):
        session_id = "chan-legacy"
        legacy = self.recordings_path / f"{session_id}.cast"
        legacy.write_text('{"version": 2}\n', encoding="utf-8")

        self.assertEqual(self.recorder.get_cast_path(session_id, "user-web"), legacy)
        self.assertIsNone(self.recorder.get_cast_path(session_id, "admin-web"))

    def test_get_recording_lists_channels(self):
        session_id = "chan-list"
        self.recorder.start_session(session_id, name="Channel Listing Test")
        self.recorder.record_output("u\n", channel="user-web")
        self.recorder.record_output("a\n", channel="admin-web")
        self.recorder.record_output("d\n", channel="user-desktop")
        self.recorder.close()

        data = self.recorder.get_recording(session_id)
        self.assertIsNotNone(data)
        self.assertIn("channels", data)
        channel_ids = {c["id"] for c in data["channels"]}
        self.assertEqual(channel_ids, {"user-web", "admin-web", "user-desktop"})
        for channel in data["channels"]:
            self.assertTrue(channel["has_cast"])
            self.assertGreater(channel["cast_size_bytes"], 0)

        self.assertTrue(data["has_cast"])
        self.assertGreater(data["cast_size_bytes"], 0)

    def test_get_recording_lists_legacy_user_web_channel(self):
        session_id = "chan-legacy-list"
        legacy = self.recordings_path / f"{session_id}.cast"
        legacy.write_text('{"version": 2}\n', encoding="utf-8")

        data = self.recorder.get_recording(session_id)
        self.assertIsNotNone(data)
        self.assertEqual([c["id"] for c in data["channels"]], ["user-web"])
        self.assertEqual(data["channels"][0]["cast_size_bytes"], legacy.stat().st_size)


if __name__ == "__main__":
    unittest.main()
