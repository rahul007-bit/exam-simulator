import os
import sys
import json
import time
import re
import threading
import subprocess
import shutil
import sqlite3
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Union


class SessionRecorder:
    """
    Manages candidate session recording:
    1. Asciinema v2 format (.cast) terminal output/input/resize streams for full terminal replay.
    2. Structured event log (.events.jsonl) tracking tasks, navigation, flags, grading, and clipboard interactions.
    3. Session metadata (.meta.json) for fast querying and post-exam review dashboards.
    """

    def __init__(self, recordings_dir: Optional[Path] = None):
        self.recordings_dir = recordings_dir or (Path(__file__).parent.parent / "recordings")
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

        self.session_id: Optional[str] = None
        self.session_name: Optional[str] = None
        self.start_timestamp: Optional[float] = None
        self.cast_file: Optional[Path] = None
        self.events_file: Optional[Path] = None
        self.meta_file: Optional[Path] = None

        self._cast_fp = None
        self._events_fp = None
        self._active = False
        self._cols = 120
        self._rows = 34
        self._browser_thread: Optional[threading.Thread] = None
        self._browser_stop_event = threading.Event()
        self._last_browser_ts = 0
        self._input_buf: Dict[str, str] = {}

    @property
    def is_active(self) -> bool:
        return self._active and self._cast_fp is not None

    def start_session(
        self,
        session_id: str,
        name: str = "CKA Exam Session",
        total_tasks: int = 0,
        time_limit_minutes: Optional[int] = None,
        target_contexts: Optional[List[str]] = None,
        questions: Optional[List[Dict[str, Any]]] = None,
        cols: int = 120,
        rows: int = 34,
        candidate_user: Optional[str] = None,
    ) -> None:
        """Initializes a new recording session and writes the asciinema v2 header."""
        with self._lock:
            self._close_files_locked()

            self.session_id = session_id
            self.session_name = name
            self.start_timestamp = time.time()
            self._cols = cols
            self._rows = rows
            candidate = candidate_user or os.getenv("EXAM_USER", "exam")

            self.cast_file = self.recordings_dir / f"{session_id}.cast"
            self.events_file = self.recordings_dir / f"{session_id}.events.jsonl"
            self.meta_file = self.recordings_dir / f"{session_id}.meta.json"

            # Open asciinema cast file
            self._cast_fp = open(self.cast_file, "a", encoding="utf-8", buffering=1)
            
            # Write asciinema v2 header if file is newly created
            if self.cast_file.stat().st_size == 0:
                header = {
                    "version": 2,
                    "width": cols,
                    "height": rows,
                    "timestamp": int(self.start_timestamp),
                    "env": {
                        "SHELL": os.getenv("SHELL", "/bin/bash"),
                        "TERM": "xterm-256color",
                        "USER": candidate,
                    },
                    "title": f"CKA Exam Session: {name} ({session_id})",
                }
                self._cast_fp.write(json.dumps(header) + "\n")
                self._cast_fp.flush()

            # Open events jsonl file
            self._events_fp = open(self.events_file, "a", encoding="utf-8", buffering=1)
            self._active = True

            # Write initial metadata file
            meta = {
                "session_id": session_id,
                "name": name,
                "candidate": candidate,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "start_timestamp": self.start_timestamp,
                "ended_at": None,
                "end_timestamp": None,
                "duration_seconds": None,
                "total_tasks": total_tasks,
                "time_limit_minutes": time_limit_minutes,
                "target_contexts": target_contexts or [],
                "status": "in_progress",
                "scorecard": None,
                "percentage": None,
                "passed": None,
                "cast_file": self.cast_file.name,
                "events_file": self.events_file.name,
            }
            with open(self.meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

        # Log session start event
        self.log_event("SESSION_START", {
            "session_id": session_id,
            "name": name,
            "total_tasks": total_tasks,
            "time_limit_minutes": time_limit_minutes,
            "contexts": target_contexts or [],
            "candidate": candidate,
            "questions": questions or [],
        })

        # Start background browser history tracker (Option 1)
        self._start_browser_tracker(candidate_user=candidate)
        self._start_redis_event_subscriber(session_id)

    def attach_or_resume(self, session_id: str, name: str = "CKA Exam Session") -> None:
        """Attaches to an existing recording or initializes it if not started."""
        with self._lock:
            if self._active and self.session_id == session_id:
                return

            self._close_files_locked()
            self.session_id = session_id
            self.session_name = name

            self.cast_file = self.recordings_dir / f"{session_id}.cast"
            self.events_file = self.recordings_dir / f"{session_id}.events.jsonl"
            self.meta_file = self.recordings_dir / f"{session_id}.meta.json"

            if self.meta_file.exists():
                try:
                    with open(self.meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    self.start_timestamp = meta.get("start_timestamp", time.time())
                except Exception:
                    self.start_timestamp = time.time()
            else:
                self.start_timestamp = time.time()

            self._cast_fp = open(self.cast_file, "a", encoding="utf-8", buffering=1)
            if self.cast_file.stat().st_size == 0:
                header = {
                    "version": 2,
                    "width": self._cols,
                    "height": self._rows,
                    "timestamp": int(self.start_timestamp),
                    "env": {
                        "SHELL": os.getenv("SHELL", "/bin/bash"),
                        "TERM": "xterm-256color",
                        "USER": os.getenv("EXAM_USER", "exam"),
                    },
                    "title": f"CKA Exam Session: {name} ({session_id})",
                }
                self._cast_fp.write(json.dumps(header) + "\n")
                self._cast_fp.flush()

            self._events_fp = open(self.events_file, "a", encoding="utf-8", buffering=1)
            self._active = True
            self._start_browser_tracker(candidate_user=os.getenv("EXAM_USER", "exam"))
            self._start_redis_event_subscriber(session_id)

    def _get_rel_time(self) -> float:
        if not self.start_timestamp:
            self.start_timestamp = time.time()
        return round(max(0.0, time.time() - self.start_timestamp), 6)

    def record_output(self, data: Union[str, bytes]) -> None:
        """Records terminal output in asciinema v2 format."""
        if not self._active or not self._cast_fp:
            return

        if isinstance(data, bytes):
            data_str = data.decode("utf-8", errors="replace")
        else:
            data_str = data

        if not data_str:
            return

        rel_time = self._get_rel_time()
        record_line = json.dumps([rel_time, "o", data_str]) + "\n"

        with self._lock:
            if self._cast_fp and not self._cast_fp.closed:
                try:
                    self._cast_fp.write(record_line)
                except Exception:
                    pass

    # --- Timeline-visible typed lines (aggregated keystrokes) ---

    _INPUT_MAX_LINE = 200

    @staticmethod
    def _sanitize_input(s: str) -> str:
        """Strips ANSI escape/CSI sequences so arrow keys & colors don't pollute lines."""
        return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b.", "", s)

    def _process_input_for_events(self, actor: str, data_str: str) -> None:
        """Aggregates raw keystrokes into whole typed lines for the event timeline.

        Keeps a partial line buffered until Enter (or Ctrl-C/D) arrives, so the
        admin timeline shows 'kubectl get nodes' instead of one event per
        keystroke. Raw keystrokes remain in the .cast 'i' frames as before.
        """
        with self._lock:
            buf = self._input_buf.get(actor, "") + data_str
        buf = self._sanitize_input(buf)

        out = []
        for ch in buf:
            if ch in ("\x7f", "\b"):
                if out:
                    out.pop()
            else:
                out.append(ch)
        line = "".join(out)
        line = line.replace("\x03", "\r^C").replace("\x04", "\r^D")

        chunks = re.split(r"[\r\n]+", line)
        with self._lock:
            self._input_buf[actor] = chunks.pop()[-400:]
        for chunk in chunks:
            self._log_input_line(actor, chunk)

    def _log_input_line(self, actor: str, text: str) -> None:
        if not self._active or not text or not text.strip():
            return
        text = text[: self._INPUT_MAX_LINE]
        event = "ADMIN_TERMINAL_INPUT" if actor == "admin" else "TERMINAL_INPUT"
        self.log_event(event, {
            "actor": actor,
            "text": text,
            "length": len(text),
            "preview": text[:50],
        }, actor=actor)

    def flush_input_buffer(self, actor: Optional[str] = None) -> None:
        """Flushes any partial typed line as an event (on detach or session end)."""
        targets = [actor] if actor else list(self._input_buf.keys())
        for a in targets:
            with self._lock:
                buf = self._input_buf.pop(a, "")
            self._log_input_line(a, buf)

    def record_input(self, data: Union[str, bytes], actor: str = "candidate") -> None:
        """Records terminal keystrokes / input with actor tagging."""
        if not self._active or not self._cast_fp:
            return

        if isinstance(data, bytes):
            data_str = data.decode("utf-8", errors="replace")
        else:
            data_str = data

        if not data_str:
            return

        rel_time = self._get_rel_time()
        record_line = json.dumps([rel_time, "i", data_str]) + "\n"

        with self._lock:
            if self._cast_fp and not self._cast_fp.closed:
                try:
                    self._cast_fp.write(record_line)
                except Exception:
                    pass

        self._process_input_for_events(actor, data_str)

    def record_resize(self, cols: int, rows: int) -> None:
        """Records terminal resize event."""
        if not self._active or not self._cast_fp:
            return

        self._cols = cols
        self._rows = rows
        rel_time = self._get_rel_time()
        record_line = json.dumps([rel_time, "r", f"{cols}x{rows}"]) + "\n"

        with self._lock:
            if self._cast_fp and not self._cast_fp.closed:
                try:
                    self._cast_fp.write(record_line)
                except Exception:
                    pass

        self.log_event("TERMINAL_RESIZE", {"cols": cols, "rows": rows})

    def record_marker(self, marker_text: str) -> None:
        """Records an asciinema marker event."""
        if not self._active or not self._cast_fp:
            return

        rel_time = self._get_rel_time()
        record_line = json.dumps([rel_time, "m", marker_text]) + "\n"

        with self._lock:
            if self._cast_fp and not self._cast_fp.closed:
                try:
                    self._cast_fp.write(record_line)
                except Exception:
                    pass

    def log_event(self, event_type: str, data: Optional[Dict[str, Any]] = None, actor: str = "candidate") -> None:
        """Appends a structured event to the event log with explicit actor tracking."""
        rel_time = self._get_rel_time()
        now_iso = datetime.now(timezone.utc).isoformat()

        event_payload = {
            "timestamp": now_iso,
            "rel_time": rel_time,
            "rel_time_formatted": self.format_seconds(rel_time),
            "event": event_type,
            "actor": actor,
            "session_id": self.session_id,
            "data": data or {},
        }

        if event_type in ("SESSION_START", "TASK_DEPLOYED", "TASK_FLAGGED", "TASK_UNFLAGGED", "TASK_EVALUATION", "EXAM_SUBMITTED"):
            marker_summary = f"[{event_type}]"
            if data and "question_id" in data:
                marker_summary += f" {data.get('question_id')}"
            elif data and "task_num" in data:
                marker_summary += f" Task {data.get('task_num')}"
            self.record_marker(marker_summary)

        with self._lock:
            if self._events_fp and not self._events_fp.closed:
                try:
                    self._events_fp.write(json.dumps(event_payload) + "\n")
                except Exception:
                    pass

    def finish_session(
        self,
        session_id: Optional[str] = None,
        scorecard: Optional[List[Dict[str, Any]]] = None,
        percentage: Optional[float] = None,
        passed: Optional[bool] = None,
        total_earned: Optional[int] = None,
        total_possible: Optional[int] = None,
    ) -> None:
        """Marks the session as completed and updates metadata."""
        target_id = session_id or self.session_id
        if not target_id:
            return

        end_ts = time.time()
        start_ts = self.start_timestamp or end_ts
        duration = round(end_ts - start_ts, 1)

        # Stop browser tracker and flush final visits
        self._stop_browser_tracker()

        # Flush any partial typed lines so preceding commands appear in the
        # timeline before the submission marker.
        self.flush_input_buffer()

        self.log_event("EXAM_SUBMITTED", {
            "total_earned": total_earned,
            "total_possible": total_possible,
            "percentage": percentage,
            "passed": passed,
            "duration_seconds": duration,
        })

        meta_path = self.recordings_dir / f"{target_id}.meta.json"
        meta = {}
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                meta = {}

        meta.update({
            "session_id": target_id,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "end_timestamp": end_ts,
            "duration_seconds": duration,
            "duration_formatted": self.format_seconds(duration),
            "status": "completed",
            "scorecard": scorecard,
            "percentage": percentage,
            "passed": passed,
            "total_earned": total_earned,
            "total_possible": total_possible,
        })

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        with self._lock:
            self._close_files_locked()

    def _close_files_locked(self) -> None:
        self._stop_browser_tracker()
        self._stop_redis_event_subscriber()
        if self._cast_fp:
            try:
                self._cast_fp.flush()
                self._cast_fp.close()
            except Exception:
                pass
            self._cast_fp = None

        if self._events_fp:
            try:
                self._events_fp.flush()
                self._events_fp.close()
            except Exception:
                pass
            self._events_fp = None

        self._active = False

    def close(self) -> None:
        with self._lock:
            self._close_files_locked()

    def _start_browser_tracker(self, candidate_user: str = "exam") -> None:
        """Starts background thread polling Firefox places.sqlite for candidate URL visits."""
        if self._browser_thread and self._browser_thread.is_alive():
            return

        self._browser_stop_event.clear()
        self._last_browser_ts = int(time.time() * 1_000_000)

        def _poll_loop():
            while not self._browser_stop_event.is_set():
                try:
                    self._check_browser_history(candidate_user)
                except Exception:
                    pass
                self._browser_stop_event.wait(2.5)

        self._browser_thread = threading.Thread(target=_poll_loop, daemon=True, name="BrowserTracker")
        self._browser_thread.start()

    def _stop_browser_tracker(self, candidate_user: str = "exam") -> None:
        """Stops background browser history thread and flushes remaining visits."""
        self._browser_stop_event.set()
        t = self._browser_thread
        self._browser_thread = None
        if t and t.is_alive():
            try:
                t.join(timeout=1.0)
            except Exception:
                pass
        try:
            self._check_browser_history(candidate_user)
        except Exception:
            pass

    def _start_redis_event_subscriber(self, session_id: str) -> None:
        """Starts background subscriber for desktop Redis events:{session_id}."""
        if hasattr(self, "_redis_sub_thread") and self._redis_sub_thread and self._redis_sub_thread.is_alive():
            return

        if not hasattr(self, "_redis_stop_event"):
            self._redis_stop_event = threading.Event()
        self._redis_stop_event.clear()

        def _sub_loop():
            try:
                from core.redis_bus import bus as rbus
                client = rbus.get_sync_client()
                if not client:
                    return
                pubsub = client.pubsub()
                channel = f"events:{session_id}"
                pubsub.subscribe(channel)

                while not self._redis_stop_event.is_set():
                    try:
                        msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                        if msg and msg.get("type") == "message":
                            raw = msg.get("data", "")
                            if isinstance(raw, bytes):
                                raw = raw.decode("utf-8", errors="replace")
                            payload = json.loads(raw)
                            event_type = payload.pop("event", "DESKTOP_EVENT")
                            self.log_event(event_type, payload)
                    except Exception:
                        time.sleep(1.0)
            except Exception:
                pass

        self._redis_sub_thread = threading.Thread(target=_sub_loop, daemon=True, name=f"RedisSub-{session_id}")
        self._redis_sub_thread.start()

    def _stop_redis_event_subscriber(self) -> None:
        """Stops the Redis event subscriber thread."""
        if hasattr(self, "_redis_stop_event"):
            self._redis_stop_event.set()
        t = getattr(self, "_redis_sub_thread", None)
        self._redis_sub_thread = None
        if t and t.is_alive():
            try:
                t.join(timeout=1.0)
            except Exception:
                pass

    def _find_places_db(self, candidate_user: str = "exam") -> Optional[Path]:
        """Discovers active Firefox places.sqlite profile database.

        Covers the common Linux install layouts: distro package (~/.mozilla),
        XDG (~/.config/mozilla), Snap and Flatpak. An explicit override may be
        supplied via the ``FIREFOX_PROFILE_DIR`` env var.
        """
        override = os.getenv("FIREFOX_PROFILE_DIR")
        roots = []
        if override:
            roots.append(Path(override))
        roots.extend(
            [
                Path(f"/home/{candidate_user}/.mozilla/firefox"),
                Path(f"/home/{candidate_user}/.config/mozilla/firefox"),
                Path(f"/home/{candidate_user}/snap/firefox/common/.mozilla/firefox"),
                Path(f"/home/{candidate_user}/.var/app/org.mozilla.firefox/.mozilla/firefox"),
                Path.home() / ".mozilla/firefox",
                Path.home() / ".config/mozilla/firefox",
                Path.home() / "snap/firefox/common/.mozilla/firefox",
                Path.home() / ".var/app/org.mozilla.firefox/.mozilla/firefox",
            ]
        )

        # Prefer the profile whose places.sqlite was touched most recently.
        candidates: list[Path] = []
        for pdir in roots:
            if pdir.exists():
                candidates.extend(p for p in pdir.glob("*/places.sqlite") if p.is_file())
        if not candidates:
            return None
        try:
            return max(candidates, key=lambda p: p.stat().st_mtime)
        except OSError:
            return candidates[0]

    def _check_browser_history(self, candidate_user: str = "exam") -> None:
        """Snapshots Firefox places.sqlite and logs new visits/searches into session events."""
        if not self._active:
            return

        places_path = self._find_places_db(candidate_user)
        if not places_path or not places_path.exists():
            if os.getenv("RECORDER_DEBUG") and not getattr(self, "_browser_db_warned", False):
                self._browser_db_warned = True
                print(
                    f"[Recorder] Firefox places.sqlite not found for user "
                    f"'{candidate_user}' (set FIREFOX_PROFILE_DIR to override)",
                    flush=True,
                )
            return

        tmp_id = f"places_snap_{os.getpid()}_{threading.get_ident()}"
        tmp_db = Path(f"/tmp/{tmp_id}.sqlite")
        try:
            shutil.copy2(places_path, tmp_db)
            wal = places_path.with_name(places_path.name + "-wal")
            if wal.exists():
                shutil.copy2(wal, Path(f"/tmp/{tmp_id}.sqlite-wal"))

            conn = sqlite3.connect(f"file:{tmp_db}?mode=ro", uri=True, timeout=2.0)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url, title, last_visit_date FROM moz_places WHERE last_visit_date > ? ORDER BY last_visit_date ASC",
                (self._last_browser_ts,)
            )
            rows = cursor.fetchall()
            conn.close()

            for url, title, visit_ts in rows:
                if visit_ts > self._last_browser_ts:
                    self._last_browser_ts = visit_ts

                if not url or url.startswith(("about:", "chrome:", "blob:", "data:")):
                    continue

                parsed = urllib.parse.urlparse(url)
                # Unwrap Google redirect intermediaries
                if "google.com" in parsed.netloc and "/url" in parsed.path:
                    qs = urllib.parse.parse_qs(parsed.query)
                    target_q = qs.get("q", [None])[0]
                    if target_q and target_q.startswith("http"):
                        url = target_q
                        parsed = urllib.parse.urlparse(url)

                domain = parsed.netloc.lower()
                query_str = None

                # Detect search queries (e.g. Google, DuckDuckGo, Bing, kubernetes.io)
                if ("google." in domain or "duckduckgo." in domain or "bing." in domain) and "/search" in parsed.path:
                    qs = urllib.parse.parse_qs(parsed.query)
                    query_str = qs.get("q", [None])[0]
                elif "kubernetes.io" in domain and "/search" in parsed.path:
                    qs = urllib.parse.parse_qs(parsed.query)
                    query_str = qs.get("q", [None])[0]

                if query_str:
                    self.log_event("BROWSER_SEARCH", {
                        "query": query_str,
                        "url": url,
                        "domain": domain,
                        "title": title or f"Search: {query_str}"
                    })
                    self.record_marker(f"[BROWSER_SEARCH] {query_str}")
                else:
                    self.log_event("BROWSER_NAVIGATE", {
                        "url": url,
                        "title": title or domain,
                        "domain": domain
                    })
                    self.record_marker(f"[BROWSER_NAVIGATE] {url}")
        except Exception:
            pass
        finally:
            for suffix in ["", "-wal", "-shm"]:
                p = Path(f"/tmp/{tmp_id}.sqlite{suffix}")
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

    @staticmethod
    def format_seconds(secs: float) -> str:
        s = int(secs)
        hrs = s // 3600
        mins = (s % 3600) // 60
        sec = s % 60
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{sec:02d}"
        return f"{mins:02d}:{sec:02d}"

    def list_recordings(self) -> List[Dict[str, Any]]:
        """Returns a list of all recorded sessions sorted newest first."""
        recordings = []
        for meta_file in self.recordings_dir.glob("*.meta.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                session_id = data.get("session_id", meta_file.name.replace(".meta.json", ""))
                cast_file = self.recordings_dir / f"{session_id}.cast"
                events_file = self.recordings_dir / f"{session_id}.events.jsonl"

                cast_size = cast_file.stat().st_size if cast_file.exists() else 0
                events_count = 0
                if events_file.exists():
                    with open(events_file, "r", encoding="utf-8") as ef:
                        events_count = sum(1 for _ in ef)

                data["has_cast"] = cast_file.exists()
                data["cast_size_bytes"] = cast_size
                data["cast_size_human"] = self._human_size(cast_size)
                data["has_events"] = events_file.exists()
                data["events_count"] = events_count
                recordings.append(data)
            except Exception:
                pass

        return sorted(recordings, key=lambda x: x.get("start_timestamp") or 0, reverse=True)

    def get_recording(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Loads complete metadata and event summary for a session."""
        meta_path = self.recordings_dir / f"{session_id}.meta.json"
        cast_path = self.recordings_dir / f"{session_id}.cast"
        events_path = self.recordings_dir / f"{session_id}.events.jsonl"

        if not meta_path.exists() and not cast_path.exists() and not events_path.exists():
            return None

        meta = {}
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                meta = {}

        events = []
        if events_path.exists():
            try:
                with open(events_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            events.append(json.loads(line))
            except Exception:
                pass

        meta["session_id"] = session_id
        meta["events"] = events
        meta["events_count"] = len(events)
        meta["has_cast"] = cast_path.exists()
        meta["cast_size_bytes"] = cast_path.stat().st_size if cast_path.exists() else 0
        meta["task_timeline"] = self._build_task_timeline(events, scorecard=meta.get("scorecard"))

        return meta

    def get_events(self, session_id: str) -> List[Dict[str, Any]]:
        events_path = self.recordings_dir / f"{session_id}.events.jsonl"
        if not events_path.exists():
            return []
        events = []
        with open(events_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        return events

    def get_cast_path(self, session_id: str) -> Optional[Path]:
        cast_path = self.recordings_dir / f"{session_id}.cast"
        if cast_path.exists():
            return cast_path
        return None

    def _build_task_timeline(self, events: List[Dict[str, Any]], scorecard: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Extracts task deployment intervals and metrics from events."""
        tasks: Dict[str, Dict[str, Any]] = {}
        ordered_task_ids = []

        for evt in events:
            etype = evt.get("event")
            rel_t = evt.get("rel_time", 0.0)
            data = evt.get("data", {})

            if etype == "TASK_DEPLOYED":
                qid = data.get("question_id")
                tnum = data.get("task_num")
                if qid:
                    if qid not in tasks:
                        tasks[qid] = {
                            "question_id": qid,
                            "task_num": tnum,
                            "title": data.get("title", ""),
                            "domain": data.get("domain", ""),
                            "context": data.get("context", ""),
                            "points": data.get("points", 0),
                            "first_seen_time": rel_t,
                            "last_seen_time": rel_t,
                            "visits": 0,
                            "is_flagged": False,
                            "score": None,
                            "max_score": data.get("points", 0),
                            "passed": None,
                            "events": [],
                        }
                        ordered_task_ids.append(qid)

                    tasks[qid]["visits"] += 1
                    tasks[qid]["last_seen_time"] = rel_t
                    tasks[qid]["events"].append({
                        "event": "DEPLOYED",
                        "rel_time": rel_t,
                        "formatted_time": self.format_seconds(rel_t),
                    })

            elif etype in ("TASK_FLAGGED", "TASK_UNFLAGGED"):
                qid = data.get("question_id")
                if qid and qid in tasks:
                    tasks[qid]["is_flagged"] = (etype == "TASK_FLAGGED")
                    tasks[qid]["events"].append({
                        "event": etype,
                        "rel_time": rel_t,
                        "formatted_time": self.format_seconds(rel_t),
                    })

            elif etype == "TASK_EVALUATION":
                qid = data.get("question_id")
                if qid and qid in tasks:
                    tasks[qid]["score"] = data.get("score")
                    tasks[qid]["max_score"] = data.get("max_score")
                    tasks[qid]["passed"] = data.get("passed")
                    tasks[qid]["message"] = data.get("message")
                    tasks[qid]["events"].append({
                        "event": "EVALUATED",
                        "score": data.get("score"),
                        "max_score": data.get("max_score"),
                        "passed": data.get("passed"),
                        "message": data.get("message"),
                        "rel_time": rel_t,
                        "formatted_time": self.format_seconds(rel_t),
                    })

        if scorecard:
            scorecard_map = {item.get("id"): item for item in scorecard if item.get("id")}
            for qid, t in tasks.items():
                if t.get("score") is None and qid in scorecard_map:
                    sc = scorecard_map[qid]
                    t["score"] = sc.get("score")
                    t["max_score"] = sc.get("max_score", t.get("max_score"))
                    t["passed"] = sc.get("passed")
                    t["message"] = sc.get("message")

        return [tasks[qid] for qid in ordered_task_ids]

    def replay_cli(self, session_id: str, speed: float = 1.0, max_wait: float = 2.0) -> None:
        """Plays back an asciinema .cast terminal recording in the CLI."""
        cast_path = self.get_cast_path(session_id)
        if not cast_path:
            print(f"[Error] Recording not found: {session_id}.cast")
            return

        print(f"\n[Asciinema Replay] Starting playback of '{session_id}' (Speed: {speed}x)...")
        print("Press Ctrl+C to stop replay at any time.\n")
        time.sleep(1)

        last_time = 0.0
        try:
            with open(cast_path, "r", encoding="utf-8") as f:
                header_line = f.readline()
                try:
                    header = json.loads(header_line)
                    print(f"Recorded title: {header.get('title', 'Unknown')}")
                    print(f"Terminal size:  {header.get('width')}x{header.get('height')}\n" + "-" * 60)
                except Exception:
                    pass

                for line in f:
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        if not isinstance(record, list) or len(record) < 3:
                            continue
                        rel_time, event_type, content = record[0], record[1], record[2]
                        
                        delta = max(0.0, rel_time - last_time)
                        capped_delta = min(delta, max_wait)
                        wait_seconds = capped_delta / max(0.1, speed)
                        if wait_seconds > 0.001:
                            time.sleep(wait_seconds)
                        last_time = rel_time

                        if event_type == "o":
                            sys.stdout.write(content)
                            sys.stdout.flush()
                        elif event_type == "m":
                            sys.stdout.write(f"\n\x1b[33;1m>>> [MARKER] {content}\x1b[0m\n")
                            sys.stdout.flush()
                    except json.JSONDecodeError:
                        continue
            print("\n\n" + "-" * 60)
            print("[Asciinema Replay] Replay finished successfully.")
        except KeyboardInterrupt:
            print("\n[Asciinema Replay] Playback interrupted by user.")

    def render_recordings_table(self) -> None:
        """Renders a formatted table of all recorded sessions using rich."""
        recordings = self.list_recordings()
        if not recordings:
            print("\n[Recordings] No recorded candidate sessions found in recordings/\n")
            return

        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            table = Table(title="Candidate Session Recordings", header_style="bold cyan")
            table.add_column("Session ID", style="bold")
            table.add_column("Exam Preset", style="yellow")
            table.add_column("Candidate", style="dim")
            table.add_column("Date", style="blue")
            table.add_column("Duration", justify="center")
            table.add_column("Score", justify="center")
            table.add_column("Status", justify="center")
            table.add_column("Cast Size", justify="right")
            table.add_column("Events", justify="right")

            for r in recordings:
                sid = r.get("session_id", "unknown")
                name = r.get("name", "Mock Exam")
                cand = r.get("candidate", "exam")
                start = r.get("started_at", "")[:19].replace("T", " ")
                dur = r.get("duration_formatted") or (self.format_seconds(r.get("duration_seconds", 0)) if r.get("duration_seconds") else "--:--")
                
                pct = r.get("percentage")
                score_str = f"{pct}%" if pct is not None else "--"
                passed = r.get("passed")
                if passed is True:
                    status = "[bold green]PASS[/bold green]"
                elif passed is False:
                    status = "[bold red]FAIL[/bold red]"
                else:
                    status = "[yellow]IN PROGRESS[/yellow]" if r.get("status") == "in_progress" else "[dim]UNKNOWN[/dim]"

                cast_sz = r.get("cast_size_human", "0 B")
                ev_cnt = str(r.get("events_count", 0))

                table.add_row(sid, name, cand, start, dur, score_str, status, cast_sz, ev_cnt)

            console.print("\n")
            console.print(table)
            console.print("\n[dim]To inspect a session timeline and task breakdown: [bold]labctl review <session_id>[/bold][/dim]")
            console.print("[dim]To replay candidate terminal in terminal:        [bold]labctl replay <session_id> [--speed 2.0][/bold][/dim]\n")
        except Exception:
            print(f"\n{'SESSION ID':<24}{'NAME':<24}{'DATE':<20}{'DURATION':<12}{'SCORE':<8}{'STATUS'}")
            print("-" * 100)
            for r in recordings:
                sid = r.get("session_id", "unknown")
                name = r.get("name", "Mock Exam")[:22]
                start = r.get("started_at", "")[:19].replace("T", " ")
                dur = r.get("duration_formatted", "--:--")
                pct = f"{r.get('percentage')}%" if r.get('percentage') is not None else "--"
                st = "PASS" if r.get("passed") else ("FAIL" if r.get("passed") is False else "IN PROGRESS")
                print(f"{sid:<24}{name:<24}{start:<20}{dur:<12}{pct:<8}{st}")
            print()

    def render_review_report(self, session_id: Optional[str] = None) -> None:
        """Renders comprehensive post-exam candidate review with task timeline and event breakdown."""
        if not session_id:
            recordings = self.list_recordings()
            if not recordings:
                print("\n[Error] No candidate session recordings found to review.\n")
                return
            session_id = recordings[0]["session_id"]

        data = self.get_recording(session_id)
        if not data:
            print(f"\n[Error] Recording for session '{session_id}' not found in recordings/.\n")
            return

        try:
            from rich.console import Console
            from rich.table import Table
            from rich.panel import Panel
            console = Console()

            # Session Overview Panel
            name = data.get("name", "CKA Exam")
            cand = data.get("candidate", "exam")
            start = data.get("started_at", "")[:19].replace("T", " ")
            dur = data.get("duration_formatted") or (self.format_seconds(data.get("duration_seconds", 0)) if data.get("duration_seconds") else "--:--")
            pct = data.get("percentage")
            passed = data.get("passed")
            earned = data.get("total_earned")
            possible = data.get("total_possible")

            result_str = "[bold green]PASSED[/bold green]" if passed else ("[bold red]FAILED[/bold red]" if passed is False else "[yellow]IN PROGRESS[/yellow]")
            score_str = f"{earned}/{possible} pts ({pct}%)" if pct is not None else "Pending submission"

            overview = (
                f"[bold cyan]Session ID:[/bold cyan]    {session_id}\n"
                f"[bold cyan]Exam Name:[/bold cyan]     {name}\n"
                f"[bold cyan]Candidate:[/bold cyan]     {cand}\n"
                f"[bold cyan]Date/Time:[/bold cyan]     {start} UTC\n"
                f"[bold cyan]Duration:[/bold cyan]      {dur}\n"
                f"[bold cyan]Total Result:[/bold cyan]  {result_str} — {score_str}\n"
                f"[bold cyan]Cast File:[/bold cyan]     {data.get('has_cast')} ({self._human_size(data.get('cast_size_bytes', 0))})\n"
                f"[bold cyan]Total Events:[/bold cyan]  {data.get('events_count', 0)}"
            )
            console.print(Panel(overview, title="[bold yellow]CANDIDATE EXAM POST-REVIEW[/bold yellow]", border_style="cyan"))

            # Task Timeline Breakdown Table
            tasks = data.get("task_timeline", [])
            if tasks:
                ttable = Table(title="Task Navigation & Performance Breakdown", header_style="bold cyan")
                ttable.add_column("#", justify="center", style="bold")
                ttable.add_column("Question ID", style="dim")
                ttable.add_column("Title")
                ttable.add_column("Context", style="blue")
                ttable.add_column("Visits", justify="center")
                ttable.add_column("First Seen", justify="center")
                ttable.add_column("Last Active", justify="center")
                ttable.add_column("Flagged", justify="center")
                ttable.add_column("Score", justify="center")
                ttable.add_column("Status", justify="center")

                for t in tasks:
                    tnum = str(t.get("task_num", "-"))
                    qid = t.get("question_id", "")
                    title = t.get("title", "")
                    ctx = t.get("context", "")
                    visits = str(t.get("visits", 1))
                    first = self.format_seconds(t.get("first_seen_time", 0))
                    last = self.format_seconds(t.get("last_seen_time", 0))
                    fl = "[bold red]🚩 YES[/bold red]" if t.get("is_flagged") else "No"
                    
                    sc = t.get("score")
                    max_sc = t.get("max_score")
                    score_cell = f"{sc}/{max_sc}" if sc is not None else "--"
                    
                    tpassed = t.get("passed")
                    if tpassed is True:
                        st = "[green]PASS[/green]"
                    elif tpassed is False:
                        st = "[red]FAIL[/red]"
                    else:
                        st = "[dim]--[/dim]"

                    ttable.add_row(tnum, qid, title, ctx, visits, first, last, fl, score_cell, st)

                console.print(ttable)

            # Chronological Key Events Table
            events = data.get("events", [])
            key_events = [e for e in events if e.get("event") in ("SESSION_START", "TASK_DEPLOYED", "TASK_FLAGGED", "TASK_UNFLAGGED", "TASK_RETRY", "TASK_EVALUATION", "EXAM_SUBMITTED", "CLIPBOARD_COPY", "BROWSER_NAVIGATE", "BROWSER_SEARCH")]
            if key_events:
                etable = Table(title="Chronological Event Timeline", header_style="bold magenta")
                etable.add_column("Time", justify="center", style="bold")
                etable.add_column("Event Type", style="yellow")
                etable.add_column("Details", style="white")

                for e in key_events:
                    ftime = e.get("rel_time_formatted", self.format_seconds(e.get("rel_time", 0)))
                    etype = e.get("event", "")
                    edata = e.get("data", {})
                    
                    if etype == "SESSION_START":
                        detail = f"Started exam preset '{edata.get('name')}' with {edata.get('total_tasks')} tasks"
                    elif etype == "TASK_DEPLOYED":
                        detail = f"Switched to Task {edata.get('task_num')}: [{edata.get('question_id')}] {edata.get('title')} ({edata.get('context')})"
                    elif etype == "TASK_FLAGGED":
                        detail = f"🚩 Flagged Task {edata.get('task_num')} ({edata.get('question_id')}) for later review"
                    elif etype == "TASK_UNFLAGGED":
                        detail = f"Unflagged Task {edata.get('task_num')} ({edata.get('question_id')})"
                    elif etype == "TASK_RETRY":
                        detail = f"Reset/Retried Task {edata.get('task_num')} ({edata.get('question_id')})"
                    elif etype == "CLIPBOARD_COPY":
                        detail = f"Copied instruction snippet ({edata.get('length')} chars): '{edata.get('preview', '')[:40]}...'"
                    elif etype == "TASK_EVALUATION":
                        st = "PASS" if edata.get('passed') else "FAIL"
                        detail = f"Evaluation [{edata.get('question_id')}]: {edata.get('score')}/{edata.get('max_score')} pts ({st}) - {edata.get('message')}"
                    elif etype == "EXAM_SUBMITTED":
                        st = "PASSED" if edata.get('passed') else "FAILED"
                        detail = f"Submitted final exam! Earned {edata.get('total_earned')}/{edata.get('total_possible')} pts ({edata.get('percentage')}%) - {st}"
                    elif etype == "BROWSER_NAVIGATE":
                        title_str = f" ({edata.get('title')})" if edata.get('title') and edata.get('title') != edata.get('url') else ""
                        detail = f"🌐 Navigated: {edata.get('url')}{title_str}"
                    elif etype == "BROWSER_SEARCH":
                        detail = f"🔍 Search: \"{edata.get('query')}\" on {edata.get('domain', 'web')}"
                    else:
                        detail = str(edata)

                    etable.add_row(ftime, etype, detail)

                console.print(etable)

            console.print(f"\n[bold green]To replay full terminal keystrokes and output:[/bold green]")
            console.print(f"  [bold cyan]labctl replay {session_id} --speed 2.0[/bold cyan]\n")
        except Exception as e:
            print(f"Review for {session_id}: {e}")

    def record_shell(self, cmd: Optional[List[str]] = None, session_id: Optional[str] = None) -> int:
        """
        Launches an interactive PTY shell, intercepting and recording all stdout,
        stdin, and resize events directly into the active session's asciinema stream.
        """
        import pty
        import signal
        import shutil

        if not cmd:
            if os.geteuid() == 0:
                target_user = os.getenv("EXAM_USER", "exam")
                cmd = ["su", "-", target_user]
            else:
                cmd = [os.environ.get("SHELL", "/bin/bash")]

        if session_id:
            self.attach_or_resume(session_id)

        # If not already attached, auto-detect active session from var/session.json
        if not self._active:
            try:
                session_file = Path(__file__).parent.parent / "var" / "session.json"
                if session_file.exists():
                    with open(session_file, "r", encoding="utf-8") as f:
                        sdata = json.load(f)
                    sid = sdata.get("session_id")
                    sname = sdata.get("name", "Exam Session")
                    if sid:
                        self.attach_or_resume(sid, sname)
            except Exception:
                pass

        # If still no active exam recording, simply run the shell normally
        if not self._active or not self._cast_fp:
            return subprocess.call(cmd)

        self.record_marker("[DESKTOP_TERMINAL_START]")
        self.log_event("DESKTOP_TERMINAL_ATTACH", {"pid": os.getpid(), "cmd": cmd})

        # Capture initial dimensions
        cols, rows = shutil.get_terminal_size((120, 34))
        self.record_resize(cols, rows)

        def _master_read(fd):
            data = os.read(fd, 1024)
            if data:
                self.record_output(data)
            return data

        def _stdin_read(fd):
            data = os.read(fd, 1024)
            if data:
                self.record_input(data)
            return data

        old_handler = None
        try:
            def _sigwinch_handler(signum, frame):
                c, r = shutil.get_terminal_size((120, 34))
                self.record_resize(c, r)

            old_handler = signal.signal(signal.SIGWINCH, _sigwinch_handler)
            pty.spawn(cmd, _master_read, _stdin_read)
        except Exception:
            return 1
        finally:
            if old_handler is not None:
                try:
                    signal.signal(signal.SIGWINCH, old_handler)
                except Exception:
                    pass
            self.record_marker("[DESKTOP_TERMINAL_END]")
            self.log_event("DESKTOP_TERMINAL_DETACH", {"pid": os.getpid()})

        return 0

    @staticmethod
    def _human_size(num_bytes: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if num_bytes < 1024:
                return f"{num_bytes:.1f} {unit}"
            num_bytes /= 1024
        return f"{num_bytes:.1f} TB"


recorder = SessionRecorder()
