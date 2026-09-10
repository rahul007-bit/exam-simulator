#!/usr/bin/env python3
"""
Lightweight Redis-Driven Desktop Sidecar Agent
Runs inside cka-desktop container to provide:
1. Dynamic Registration: Registers container IP and ports in Redis.
2. Bidirectional Clipboard Sync: Subscribes to clipboard:{session_id} and publishes local X11 copies.
3. Documentation/Activity Telemetry: Emits active window and Firefox history
   (browser navigation/search) events to events:{session_id}.
4. Heartbeat: Keeps desktop:{session_id}:alive key refreshed.
"""

import os
import re
import shutil
import sqlite3
import sys
import time
import json
import signal
import socket
import subprocess
import threading
import urllib.parse
from pathlib import Path
from typing import Optional

try:
    import redis
except ImportError:
    print("[DeskAgent] Error: redis python package is required.")
    sys.exit(1)

SESSION_ID = os.getenv("SESSION_ID", "default")
REDIS_HOST = os.getenv("REDIS_HOST", "172.17.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
DISPLAY = os.getenv("DISPLAY", ":1")

os.environ["DISPLAY"] = DISPLAY


def get_container_ip() -> str:
    """Discovers internal container IP on docker0 network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((REDIS_HOST, REDIS_PORT))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            out = subprocess.check_output(["hostname", "-i"], timeout=2).decode().strip()
            return out.split()[0]
        except Exception:
            return "127.0.0.1"


class DeskAgent:
    def __init__(self):
        self.session_id = SESSION_ID
        self.redis_host = REDIS_HOST
        self.redis_port = REDIS_PORT
        self.container_ip = get_container_ip()
        self.running = True

        self.r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
        self.r_bytes = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=False)
        self._last_seen_clip = ""
        self._last_seen_prim = ""
        self._last_published = ""
        self._last_window_title = ""
        self._input_buf = ""
        self._input_last_ts = 0.0
        self._input_lock = threading.Lock()
        self._keymap = {}
        self._last_browser_ts = int(time.time() * 1_000_000)

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        print(f"[DeskAgent] Caught signal {signum}, cleaning up...")
        self.running = False
        self.cleanup()
        sys.exit(0)

    def register(self):
        """Registers container network location in Redis."""
        key = f"desktop:{self.session_id}"
        mapping = {
            "host": self.container_ip,
            "vnc_port": "5901",
            "ws_port": "6080",
            "registered_at": str(time.time()),
        }
        self.r.hset(key, mapping=mapping)
        self.r.expire(key, 86400)
        self.r.set(f"desktop:{self.session_id}:alive", "1", ex=25)
        print(f"[DeskAgent] Registered session '{self.session_id}' at {self.container_ip}:5901 in Redis.")

    def cleanup(self):
        """Removes registration upon container stop."""
        try:
            self._flush_desktop_input()
        except Exception:
            pass
        try:
            self.r.delete(f"desktop:{self.session_id}")
            self.r.delete(f"desktop:{self.session_id}:alive")
            print(f"[DeskAgent] Deregistered session '{self.session_id}' from Redis.")
        except Exception:
            pass

    # --- Inbound Clipboard (Web -> X11) ---

    def start_inbound_clipboard_listener(self):
        def _listen():
            pubsub = self.r.pubsub()
            channels = [
                f"clipboard:{self.session_id}",
                "clipboard:active",
                f"session:{self.session_id}",
                "session:active",
            ]
            pubsub.subscribe(*channels)
            print(f"[DeskAgent] Subscribed to Redis channels {channels} for inbound clipboard.")

            while self.running:
                try:
                    msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if msg and msg.get("type") == "message":
                        raw_data = msg.get("data", "")
                        text_to_set = ""
                        try:
                            parsed = json.loads(raw_data)
                            if parsed.get("source") == "desktop":
                                # Ignore our own echoes
                                continue
                            if parsed.get("type") == "clipboard_sync" and parsed.get("source") == "desktop":
                                continue
                            text_to_set = parsed.get("text", "")
                        except Exception:
                            text_to_set = raw_data

                        if text_to_set and text_to_set != self._last_published:
                            self._last_published = text_to_set
                            self._last_seen_clip = text_to_set
                            self._last_seen_prim = text_to_set
                            self._set_x11_clipboard(text_to_set)
                except Exception:
                    time.sleep(1.0)

        t = threading.Thread(target=_listen, daemon=True, name="InboundClipboard")
        t.start()

    def _set_x11_clipboard(self, text: str):
        """Pushes text into X11 CLIPBOARD and PRIMARY selections."""
        for sel in ("clipboard", "primary"):
            try:
                proc = subprocess.Popen(
                    ["xclip", "-selection", sel],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                proc.communicate(input=text.encode("utf-8"), timeout=1.5)
            except Exception:
                pass

    # --- Outbound Clipboard (X11 -> Redis) ---

    def _read_x11_selection(self, sel: str) -> str:
        """Reads specific X11 selection buffer."""
        try:
            out = subprocess.check_output(
                ["xclip", "-o", "-selection", sel],
                stderr=subprocess.DEVNULL,
                timeout=0.6,
            )
            return out.decode("utf-8", errors="replace").strip()
        except Exception:
            return ""

    def start_outbound_clipboard_poller(self):
        def _poll():
            # Initial seed from X11 selections to avoid spurious triggers on startup
            self._last_seen_clip = self._read_x11_selection("clipboard")
            self._last_seen_prim = self._read_x11_selection("primary")
            self._last_published = self._last_seen_clip or self._last_seen_prim
            if self._last_published:
                try:
                    self.r.set(f"clipboard:{self.session_id}", self._last_published, ex=3600)
                    self.r.set("clipboard:active", self._last_published, ex=3600)
                except Exception:
                    pass

            while self.running:
                try:
                    clip_val = self._read_x11_selection("clipboard")
                    prim_val = self._read_x11_selection("primary")

                    new_selection = None
                    # Prioritize explicit CLIPBOARD changes (Ctrl+C / Ctrl+Shift+C / Copy menu)
                    if clip_val and clip_val != self._last_seen_clip:
                        self._last_seen_clip = clip_val
                        new_selection = clip_val
                    # Otherwise check PRIMARY (mouse text highlights)
                    elif prim_val and prim_val != self._last_seen_prim:
                        self._last_seen_prim = prim_val
                        new_selection = prim_val

                    # Only process if changed from our last published clipboard
                    if new_selection and new_selection != self._last_published:
                        self._last_published = new_selection

                        # 1. Update Redis keys so GET /api/clipboard immediately returns this text
                        self.r.set(f"clipboard:{self.session_id}", new_selection, ex=3600)
                        self.r.set("clipboard:active", new_selection, ex=3600)

                        # 2. Publish clipboard_update to session channels for real-time WebSocket delivery
                        payload = {
                            "type": "clipboard_update",
                            "source": "desktop",
                            "text": new_selection,
                            "timestamp": time.time(),
                        }
                        payload_json = json.dumps(payload)
                        self.r.publish(f"session:{self.session_id}", payload_json)
                        if self.session_id != "active":
                            self.r.publish("session:active", payload_json)
                        self.r.publish(f"clipboard:{self.session_id}", payload_json)
                        self.r.publish("clipboard:active", payload_json)

                        # 3. Log event for exam recording
                        event_payload = {
                            "event": "CLIPBOARD_COPY",
                            "source": "desktop",
                            "char_count": len(new_selection),
                            "preview": new_selection[:40] + ("..." if len(new_selection) > 40 else ""),
                        }
                        self.r.publish(f"events:{self.session_id}", json.dumps(event_payload))
                except Exception:
                    pass
                time.sleep(0.6)

        t = threading.Thread(target=_poll, daemon=True, name="OutboundClipboard")
        t.start()

    # --- Telemetry (Active Window / Browser Visits) ---

    def start_window_telemetry_poller(self):
        def _poll():
            while self.running:
                try:
                    out = subprocess.check_output(
                        ["xdotool", "getactivewindow", "getwindowname"],
                        stderr=subprocess.DEVNULL,
                        timeout=1.0,
                    ).decode("utf-8", errors="replace").strip()

                    if out and out != self._last_window_title:
                        self._last_window_title = out
                        app_hint = "browser" if "firefox" in out.lower() or "mozilla" in out.lower() else "desktop"
                        # Browser activity is covered by the dedicated Firefox
                        # history poller (BROWSER_NAVIGATE / BROWSER_SEARCH), so
                        # skip browser window-focus events to avoid duplicates.
                        if app_hint != "browser":
                            event_payload = {
                                "event": "WINDOW_FOCUS",
                                "title": out,
                                "app": app_hint,
                                "timestamp": time.time(),
                            }
                            self.r.publish(f"events:{self.session_id}", json.dumps(event_payload))
                except Exception:
                    pass
                time.sleep(3.0)

        t = threading.Thread(target=_poll, daemon=True, name="WindowTelemetry")
        t.start()

    # --- Browser History Telemetry (Firefox places.sqlite inside the container) ---

    def _find_firefox_places(self) -> Optional[Path]:
        """Locate the container-local Firefox places.sqlite (most recently used)."""
        home = Path.home()
        roots = [
            Path("/home/exam/.mozilla/firefox"),
            Path("/home/exam/.config/mozilla/firefox"),
            Path("/home/exam/snap/firefox/common/.mozilla/firefox"),
            home / ".mozilla/firefox",
            home / ".config/mozilla/firefox",
            home / "snap/firefox/common/.mozilla/firefox",
        ]
        candidates = []
        for root in roots:
            if root.exists():
                candidates.extend(p for p in root.glob("*/places.sqlite") if p.is_file())
        if not candidates:
            return None
        try:
            return max(candidates, key=lambda p: p.stat().st_mtime)
        except OSError:
            return candidates[0]

    def _check_browser_history(self) -> None:
        """Publishes new Firefox visits/searches to events:{session_id}."""
        places_path = self._find_firefox_places()
        if not places_path or not places_path.exists():
            return

        tmp_db = Path(f"/tmp/places_snap_{os.getpid()}_{threading.get_ident()}.sqlite")
        try:
            shutil.copy2(places_path, tmp_db)
            wal = places_path.with_name(places_path.name + "-wal")
            if wal.exists():
                shutil.copy2(wal, Path(f"{tmp_db}-wal"))

            conn = sqlite3.connect(f"file:{tmp_db}?mode=ro", uri=True, timeout=2.0)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT url, title, last_visit_date FROM moz_places "
                "WHERE last_visit_date > ? ORDER BY last_visit_date ASC",
                (self._last_browser_ts,),
            )
            rows = cursor.fetchall()
            conn.close()

            for url, title, visit_ts in rows:
                if visit_ts and visit_ts > self._last_browser_ts:
                    self._last_browser_ts = visit_ts
                if not url or url.startswith(("about:", "chrome:", "blob:", "data:")):
                    continue

                parsed = urllib.parse.urlparse(url)
                domain = parsed.netloc.lower()
                query_str = None
                if (
                    "google." in domain or "duckduckgo." in domain or "bing." in domain
                ) and "/search" in parsed.path:
                    query_str = urllib.parse.parse_qs(parsed.query).get("q", [None])[0]
                elif "kubernetes.io" in domain and "/search" in parsed.path:
                    query_str = urllib.parse.parse_qs(parsed.query).get("q", [None])[0]

                if query_str:
                    payload = {
                        "event": "BROWSER_SEARCH",
                        "query": query_str,
                        "url": url,
                        "domain": domain,
                        "title": title or f"Search: {query_str}",
                        "timestamp": time.time(),
                    }
                else:
                    payload = {
                        "event": "BROWSER_NAVIGATE",
                        "url": url,
                        "title": title or domain,
                        "domain": domain,
                        "timestamp": time.time(),
                    }
                self.r.publish(f"events:{self.session_id}", json.dumps(payload))
        except Exception:
            pass
        finally:
            for suffix in ["", "-wal", "-shm"]:
                p = Path(f"{tmp_db}{suffix}")
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

    def start_browser_history_poller(self):
        """Polls the local Firefox history and publishes browser events."""
        self._last_browser_ts = int(time.time() * 1_000_000)

        def _poll():
            while self.running:
                try:
                    self._check_browser_history()
                except Exception:
                    pass
                time.sleep(3.0)

        t = threading.Thread(target=_poll, daemon=True, name="BrowserHistory")
        t.start()

    # --- Desktop Keystroke Capture (XInput2) ---

    _KEYSYM_SPECIAL = {
        "space": " ", "minus": "-", "equal": "=", "bracketleft": "[",
        "bracketright": "]", "semicolon": ";", "apostrophe": "'",
        "grave": "`", "backslash": "\\", "comma": ",", "period": ".",
        "slash": "/", "KP_Decimal": ".", "KP_Add": "+", "KP_Subtract": "-",
        "KP_Multiply": "*", "KP_Divide": "/",
        "KP_0": "0", "KP_1": "1", "KP_2": "2", "KP_3": "3", "KP_4": "4",
        "KP_5": "5", "KP_6": "6", "KP_7": "7", "KP_8": "8", "KP_9": "9",
    }

    @classmethod
    def _keysym_to_char(cls, name: str) -> Optional[str]:
        """Maps an X keysym name to its printable character (None if not printable)."""
        if not name:
            return None
        if name.startswith(("Shift_", "Control_", "Alt_", "Meta_", "Super_",
                            "Hyper_", "ISO_", "dead_", "XF86")):
            return None
        if name in ("Num_Lock", "Caps_Lock", "Scroll_Lock", "Multi_key",
                    "Mode_switch", "Begin", "KP_Begin", "KP_Separator"):
            return None
        if re.fullmatch(r"F\d{1,2}", name):
            return None
        if name in cls._KEYSYM_SPECIAL:
            return cls._KEYSYM_SPECIAL[name]
        if len(name) == 1 and name.isprintable():
            return name
        if name.startswith("U") and len(name) == 6:
            try:
                ch = chr(int(name[1:], 16))
                return ch if ch.isprintable() else None
            except ValueError:
                return None
        return None

    def _refresh_keymap(self):
        """Caches keycode -> (plain_keysym, shifted_keysym) from xmodmap."""
        keymap = {}
        try:
            out = subprocess.check_output(["xmodmap", "-pke"],
                                          stderr=subprocess.DEVNULL, timeout=5)
            for line in out.decode("utf-8", errors="replace").splitlines():
                m = re.match(r"keycode\s+(\d+)\s+=\s*(.*)", line)
                if m:
                    syms = m.group(2).split()
                    if syms:
                        keymap[int(m.group(1))] = (syms[0], syms[1] if len(syms) > 1 else syms[0])
        except Exception:
            pass
        self._keymap = keymap

    def _translate_key(self, keycode: int, mods: int):
        """
        Translates an XI2 key event to a stroke: a character, '\\t',
        the FLUSH marker ('\\n'), the BACKSPACE marker ('\\b'),
        the INTR marker ('^C'), or None (ignore).
        """
        entry = self._keymap.get(keycode)
        if not entry:
            return None
        shift = bool(mods & 0x1)
        lock = bool(mods & 0x2)
        ctrl = bool(mods & 0x4)
        plain, shifted = entry[0], entry[1]
        if ctrl:
            if shift:
                # ctrl+shift = terminal copy/paste chord, not typed text
                return None
            if plain in ("c", "C"):
                return "^C"
            return None
        if plain in ("Return", "KP_Enter"):
            return "\n"
        if plain == "BackSpace":
            return "\b"
        if shift or (lock and len(plain) == 1 and plain.isalpha()):
            name = shifted
        else:
            name = plain
        if name in ("Tab",):
            return "\t"
        return self._keysym_to_char(name)

    def _active_window_info(self) -> tuple:
        """Best-effort (window title, app hint) for the currently focused window."""
        title, cls = "", ""
        for args in (("getwindowname",), ("getwindowclassname",)):
            try:
                out = subprocess.check_output(
                    ["xdotool", "getactivewindow", args[0]],
                    stderr=subprocess.DEVNULL, timeout=1.0)
                val = out.decode("utf-8", errors="replace").strip()
                if args[0] == "getwindowname":
                    title = val
                else:
                    cls = val
            except Exception:
                pass
        low = f"{cls} {title}".lower()
        if "terminal" in low or "xterm" in low or "console" in low:
            app = "terminal"
        elif "firefox" in low or "mozilla" in low:
            app = "browser"
        else:
            app = "desktop"
        return (title or self._last_window_title or "unknown", app)

    def _publish_desktop_input(self, text: str):
        """Publishes an aggregated typed line to the session event channel."""
        if not text:
            return
        title, app = self._active_window_info()
        payload = {
            "event": "DESKTOP_TERMINAL_INPUT",
            "text": text,
            "window": title,
            "app": app,
            "timestamp": time.time(),
        }
        try:
            self.r.publish(f"events:{self.session_id}", json.dumps(payload))
        except Exception:
            pass

    def _flush_desktop_input(self, force: bool = False):
        with self._input_lock:
            text = self._input_buf
            self._input_buf = ""
        if text or force:
            self._publish_desktop_input(text)

    def _handle_desktop_key(self, stroke: str):
        with self._input_lock:
            if stroke == "\n":
                text = self._input_buf
                self._input_buf = ""
                self._input_last_ts = time.time()
            elif stroke == "\b":
                self._input_buf = self._input_buf[:-1]
                self._input_last_ts = time.time()
                return
            elif stroke == "^C":
                text = (self._input_buf + "^C") if self._input_buf else "^C"
                self._input_buf = ""
                self._input_last_ts = time.time()
            else:
                self._input_buf += stroke
                self._input_last_ts = time.time()
                if len(self._input_buf) >= 200:
                    text = self._input_buf
                    self._input_buf = ""
                else:
                    return
        self._publish_desktop_input(text)

    def _key_input_loop(self):
        """
        Aggregates desktop keystrokes (XInput2 events on the root window) into
        whole typed lines and publishes DESKTOP_TERMINAL_INPUT events, mirroring
        the web-terminal TERMINAL_INPUT capture. Strokes are attributed to the
        focused window at flush time.
        """
        if not self._keymap:
            self._refresh_keymap()
        proc = None
        try:
            proc = subprocess.Popen(["xinput", "test-xi2", "--root"],
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    text=True, bufsize=1)
            self._last_window_title = self._active_window_info()[0]
            in_keypress = False
            keycode = None
            mods = 0
            for line in proc.stdout:
                line = line.rstrip("\n")
                if line.startswith("EVENT type"):
                    in_keypress = "(KeyPress)" in line
                    if in_keypress:
                        keycode, mods = None, 0
                    continue
                if not in_keypress:
                    continue
                m = re.search(r"detail:\s+(\d+)", line)
                if m:
                    keycode = int(m.group(1))
                    continue
                m = re.search(r"modifiers:.*base\s+(\S+)", line)
                if m and keycode is not None:
                    raw = m.group(1)
                    try:
                        mods = int(raw, 16) if raw.startswith("0x") else int(raw)
                    except ValueError:
                        mods = 0
                    stroke = self._translate_key(keycode, mods)
                    keycode = None
                    if stroke is not None:
                        self._handle_desktop_key(stroke)
        except Exception:
            pass
        finally:
            if proc:
                try:
                    proc.terminate()
                except Exception:
                    pass
            self._flush_desktop_input()

    def start_key_input_monitor(self):
        if not self._keymap:
            self._refresh_keymap()
        t = threading.Thread(target=self._key_input_loop, daemon=True, name="KeyInput")
        t.start()

    # --- Heartbeat Loop ---

    def run_heartbeat_loop(self):
        while self.running:
            try:
                self.r.set(f"desktop:{self.session_id}:alive", "1", ex=25)
            except Exception:
                pass
            try:
                with self._input_lock:
                    stale = self._input_buf and (time.time() - self._input_last_ts) > 10.0
                    if stale:
                        text = self._input_buf
                        self._input_buf = ""
                if stale:
                    self._publish_desktop_input(text)
            except Exception:
                pass
            time.sleep(10.0)


def main():
    agent = DeskAgent()
    retries = 30
    while retries > 0:
        try:
            subprocess.check_call(["xdpyinfo"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            break
        except Exception:
            time.sleep(0.5)
            retries -= 1

    agent.register()
    agent.start_inbound_clipboard_listener()
    agent.start_outbound_clipboard_poller()
    agent.start_window_telemetry_poller()
    agent.start_browser_history_poller()
    agent.start_key_input_monitor()

    print("[DeskAgent] Desktop agent running successfully.")
    agent.run_heartbeat_loop()


if __name__ == "__main__":
    main()
