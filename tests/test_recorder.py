import os
import json
import time
import tempfile
import unittest
from pathlib import Path

from core.recorder import SessionRecorder
from core.models import Question, Difficulty, Domain, ExamSession
from core.loader import QuestionLoader
from core.deployer import LabDeployer


class TestSessionRecorder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.recordings_path = Path(self.temp_dir.name)
        self.recorder = SessionRecorder(recordings_dir=self.recordings_path)

    def tearDown(self):
        self.recorder.close()
        self.temp_dir.cleanup()

    def test_start_session_creates_asciinema_v2_header_and_meta(self):
        session_id = "test-session-001"
        self.recorder.start_session(
            session_id=session_id,
            name="Test Mock Exam",
            total_tasks=3,
            time_limit_minutes=60,
            target_contexts=["k3d-cka"],
            cols=100,
            rows=30,
            candidate_user="test-candidate",
        )

        self.assertTrue(self.recorder.is_active)
        self.assertEqual(self.recorder.session_id, session_id)

        # Check cast file header
        cast_path = self.recordings_path / f"{session_id}.user-web.cast"
        self.assertTrue(cast_path.exists())
        with open(cast_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            header = json.loads(first_line)
            self.assertEqual(header["version"], 2)
            self.assertEqual(header["width"], 100)
            self.assertEqual(header["height"], 30)
            self.assertIn("Test Mock Exam", header["title"])
            self.assertEqual(header["env"]["USER"], "test-candidate")

        # Check metadata file
        meta_path = self.recordings_path / f"{session_id}.meta.json"
        self.assertTrue(meta_path.exists())
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            self.assertEqual(meta["session_id"], session_id)
            self.assertEqual(meta["total_tasks"], 3)
            self.assertEqual(meta["candidate"], "test-candidate")
            self.assertEqual(meta["status"], "in_progress")

        # Check events file has SESSION_START
        events_path = self.recordings_path / f"{session_id}.events.jsonl"
        self.assertTrue(events_path.exists())
        with open(events_path, "r", encoding="utf-8") as f:
            line = f.readline()
            evt = json.loads(line)
            self.assertEqual(evt["event"], "SESSION_START")
            self.assertEqual(evt["session_id"], session_id)
            self.assertEqual(evt["data"]["name"], "Test Mock Exam")

    def test_record_output_and_input_streams(self):
        session_id = "test-session-io"
        self.recorder.start_session(session_id=session_id, name="I/O Test")

        # Record output (string and bytes)
        self.recorder.record_output("echo 'hello world'\n")
        self.recorder.record_output(b"binary \x1b[32mgreen\x1b[0m output\n")

        # Record input
        self.recorder.record_input("kubectl get pods\r")
        self.recorder.record_input(b"k get nodes\n")

        # Record resize
        self.recorder.record_resize(120, 40)

        self.recorder.close()

        cast_path = self.recordings_path / f"{session_id}.user-web.cast"
        with open(cast_path, "r", encoding="utf-8") as f:
            lines = [json.loads(line.strip()) for line in f if line.strip()]

        # Line 0 is header
        self.assertIsInstance(lines[0], dict)
        self.assertEqual(lines[0]["version"], 2)

        # Subsequent lines are event records [time, type, data]
        event_types = [item[1] for item in lines[1:]]
        self.assertIn("o", event_types)
        self.assertIn("i", event_types)
        self.assertIn("r", event_types)

        # Verify output content
        outputs = [item[2] for item in lines[1:] if item[1] == "o"]
        self.assertIn("echo 'hello world'\n", outputs)
        self.assertTrue(any("green" in o for o in outputs))

        # Verify resize
        resizes = [item[2] for item in lines[1:] if item[1] == "r"]
        self.assertEqual(resizes[0], "120x40")

    def test_event_logging_and_task_timeline(self):
        session_id = "test-session-timeline"
        self.recorder.start_session(session_id=session_id, name="Timeline Test", total_tasks=2)

        time.sleep(0.01)
        self.recorder.log_event("TASK_DEPLOYED", {
            "task_num": 1,
            "question_id": "TR-001",
            "title": "Fix crashloop pod",
            "domain": "troubleshooting",
            "context": "k3d-cka",
            "points": 4,
        })

        time.sleep(0.01)
        self.recorder.log_event("TASK_FLAGGED", {
            "task_num": 1,
            "question_id": "TR-001",
        })

        time.sleep(0.01)
        self.recorder.log_event("TASK_DEPLOYED", {
            "task_num": 2,
            "question_id": "CA-001",
            "title": "Etcd backup",
            "domain": "cluster-arch",
            "context": "kubeadm-vms",
            "points": 5,
        })

        time.sleep(0.01)
        self.recorder.log_event("TASK_EVALUATION", {
            "task_num": 2,
            "question_id": "CA-001",
            "score": 5,
            "max_score": 5,
            "passed": True,
            "message": "Snapshot backup successfully created",
        })

        time.sleep(0.01)
        self.recorder.finish_session(
            session_id=session_id,
            scorecard=[
                {"task_num": 1, "id": "TR-001", "score": 0, "max_score": 4, "passed": False},
                {"task_num": 2, "id": "CA-001", "score": 5, "max_score": 5, "passed": True},
            ],
            percentage=55.5,
            passed=False,
            total_earned=5,
            total_possible=9,
        )

        recording_data = self.recorder.get_recording(session_id)
        self.assertIsNotNone(recording_data)
        self.assertEqual(recording_data["status"], "completed")
        self.assertEqual(recording_data["percentage"], 55.5)
        self.assertFalse(recording_data["passed"])
        self.assertEqual(recording_data["total_earned"], 5)

        # Test task timeline aggregation
        timeline = recording_data["task_timeline"]
        self.assertEqual(len(timeline), 2)
        
        tr_task = next(t for t in timeline if t["question_id"] == "TR-001")
        self.assertEqual(tr_task["task_num"], 1)
        self.assertTrue(tr_task["is_flagged"])

        ca_task = next(t for t in timeline if t["question_id"] == "CA-001")
        self.assertEqual(ca_task["task_num"], 2)
        self.assertTrue(ca_task["passed"])
        self.assertEqual(ca_task["score"], 5)

    def test_list_recordings(self):
        self.recorder.start_session("session-a", name="Exam A")
        self.recorder.finish_session("session-a", percentage=100.0, passed=True)

        self.recorder.start_session("session-b", name="Exam B")
        self.recorder.finish_session("session-b", percentage=50.0, passed=False)

        recs = self.recorder.list_recordings()
        self.assertEqual(len(recs), 2)
        session_ids = [r["session_id"] for r in recs]
        self.assertIn("session-a", session_ids)
        self.assertIn("session-b", session_ids)

    def test_deployer_integration_with_recorder(self):
        from unittest.mock import patch
        from core.redis_bus import bus as redis_bus
        session_file = self.recordings_path / "test_session.json"
        sets_dir = self.recordings_path / "sets"
        deployer = LabDeployer(session_file=session_file, sets_dir=sets_dir)
        deployer._cleanup_cluster_resources = lambda *args, **kwargs: None
        redis_bus._mem_session_states = {}
        redis_bus._mem_active_session_id = None

        q1 = Question(
            id="TR-TEST-1",
            title="Fix Test Pod 1",
            domain=Domain.TROUBLESHOOTING,
            difficulty=Difficulty.EASY,
            points=3,
            target_context="k3d-cka",
            description="Test question 1",
            namespace="default",
        )
        q2 = Question(
            id="TR-TEST-2",
            title="Fix Test Pod 2",
            domain=Domain.TROUBLESHOOTING,
            difficulty=Difficulty.MEDIUM,
            points=5,
            target_context="k3d-cka",
            description="Test question 2",
            namespace="default",
        )

        # Deploy sequential exam
        with patch.object(redis_bus, "is_available", return_value=False), \
             patch.object(redis_bus, "get_sync_client", return_value=None):
            session = deployer.deploy_sequential([q1, q2], session_name="Integration Exam")
            self.assertIsNotNone(session)
            self.assertEqual(session.current_index, 0)

            # Deploy next step
            deployer.deploy_step(session, 1)
            self.assertEqual(session.current_index, 1)

            # Clear session
            deployer.clear_session(cleanup_cluster=False)
            self.assertIsNone(redis_bus.get_active_session_id())
            self.assertIsNone(redis_bus.get_session_state())
            self.assertFalse(session_file.exists())

    def test_web_recording_endpoints(self):
        from web.api.routes.recordings import (
            list_recordings_endpoint,
            get_recording_detail_endpoint,
            get_recording_cast_endpoint,
            get_recording_events_endpoint,
            log_client_event_endpoint,
        )
        from web.api.schemas import ClientEventRequest

        session_id = "test-web-session"
        from core.recorder import recorder as global_recorder
        global_recorder.start_session(session_id, name="Web Test Session")
        global_recorder.record_output("web terminal output test\n")
        global_recorder.log_event("CUSTOM_TEST_EVENT", {"foo": "bar"})
        global_recorder.finish_session(session_id, percentage=80.0, passed=True)

        # 1. list_recordings_endpoint
        res_list = list_recordings_endpoint()
        self.assertIn("recordings", res_list)
        self.assertTrue(any(r["session_id"] == session_id for r in res_list["recordings"]))

        # 2. get_recording_detail_endpoint
        res_detail = get_recording_detail_endpoint(session_id)
        self.assertEqual(res_detail["session_id"], session_id)
        self.assertEqual(res_detail["percentage"], 80.0)

        # 3. get_recording_cast_endpoint
        res_cast = get_recording_cast_endpoint(session_id)
        self.assertTrue(hasattr(res_cast, "path"))

        # 4. get_recording_events_endpoint
        res_events = get_recording_events_endpoint(session_id)
        self.assertEqual(res_events["session_id"], session_id)
        event_names = [e["event"] for e in res_events["events"]]
        self.assertIn("CUSTOM_TEST_EVENT", event_names)

        # 5. log_client_event_endpoint
        req = ClientEventRequest(event_type="TAB_SWITCH", data={"tab": "terminal"})
        res_client_evt = log_client_event_endpoint(session_id, req)
        self.assertEqual(res_client_evt["status"], "ok")

    def test_record_shell_execution(self):
        session_id = "test-shell-session"
        self.recorder.start_session(session_id=session_id, name="Shell Test")
        rc = self.recorder.record_shell(cmd=["bash", "-c", "echo RECORD_SHELL_TEST_OK"], session_id=session_id)
        self.assertEqual(rc, 0)
        self.recorder.finish_session(session_id)

        cast_file = self.recordings_path / f"{session_id}.user-web.cast"
        self.assertTrue(cast_file.exists())
        with open(cast_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("RECORD_SHELL_TEST_OK", content)
        self.assertIn("[DESKTOP_TERMINAL_START]", content)
        self.assertIn("[DESKTOP_TERMINAL_END]", content)

    def test_browser_history_tracking(self):
        import sqlite3
        session_id = "test-browser-session"
        self.recorder.start_session(session_id=session_id, name="Browser Test")

        # Mock a Firefox places.sqlite database
        firefox_dir = Path(self.temp_dir.name) / ".config" / "mozilla" / "firefox" / "test.default"
        firefox_dir.mkdir(parents=True, exist_ok=True)
        places_db = firefox_dir / "places.sqlite"

        conn = sqlite3.connect(str(places_db))
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT, title TEXT, last_visit_date INTEGER)")
        now_micro = int(time.time() * 1_000_000) + 10_000
        cursor.execute("INSERT INTO moz_places VALUES (1, 'https://kubernetes.io/docs/concepts/storage/persistent-volumes/', 'Persistent Volumes | Kubernetes', ?)", (now_micro,))
        cursor.execute("INSERT INTO moz_places VALUES (2, 'https://kubernetes.io/search/?q=pvc+hostpath', 'Search | Kubernetes', ?)", (now_micro + 1000,))
        conn.commit()
        conn.close()

        # Point _find_places_db to our mock
        original_find = self.recorder._find_places_db
        self.recorder._find_places_db = lambda user: places_db

        try:
            self.recorder._check_browser_history("mockuser")
            self.recorder.finish_session(session_id)

            events_path = self.recordings_path / f"{session_id}.events.jsonl"
            self.assertTrue(events_path.exists())
            with open(events_path, "r", encoding="utf-8") as f:
                lines = [json.loads(line) for line in f]

            event_types = [e["event"] for e in lines]
            self.assertIn("BROWSER_NAVIGATE", event_types)
            self.assertIn("BROWSER_SEARCH", event_types)

            search_evts = [e for e in lines if e["event"] == "BROWSER_SEARCH"]
            self.assertEqual(search_evts[0]["data"]["query"], "pvc hostpath")
        finally:
            self.recorder._find_places_db = original_find


if __name__ == "__main__":
    unittest.main()
