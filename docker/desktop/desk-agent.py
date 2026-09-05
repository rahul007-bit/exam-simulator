#!/usr/bin/env python3
"""
Lightweight Redis-Driven Desktop Sidecar Agent
Runs inside cka-desktop container to provide:
1. Dynamic Registration: Registers container IP and ports in Redis.
2. Bidirectional Clipboard Sync: Subscribes to clipboard:{session_id} and publishes local X11 copies.
3. Documentation/Activity Telemetry: Emits active window and browser title changes to events:{session_id}.
4. Heartbeat: Keeps desktop:{session_id}:alive key refreshed.
"""

import os
import sys
import time
import json
import signal
import socket
import subprocess
import threading
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
        self._last_copied_text = ""
        self._last_window_title = ""

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

                        if text_to_set and text_to_set != self._last_copied_text:
                            self._last_copied_text = text_to_set
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

    def _get_x11_clipboard(self) -> Optional[str]:
        """Reads current X11 selection."""
        try:
            out = subprocess.check_output(
                ["xclip", "-o", "-selection", "clipboard"],
                stderr=subprocess.DEVNULL,
                timeout=1.0,
            )
            return out.decode("utf-8", errors="replace")
        except Exception:
            return None

    def start_outbound_clipboard_poller(self):
        def _poll():
            while self.running:
                try:
                    current_clip = self._get_x11_clipboard()
                    if current_clip and current_clip != self._last_copied_text:
                        self._last_copied_text = current_clip
                        payload = {
                            "type": "clipboard_sync",
                            "source": "desktop",
                            "text": current_clip,
                            "timestamp": time.time(),
                        }
                        self.r.publish(f"clipboard:{self.session_id}", json.dumps(payload))
                        event_payload = {
                            "event": "CLIPBOARD_COPY",
                            "source": "desktop",
                            "char_count": len(current_clip),
                            "preview": current_clip[:40] + ("..." if len(current_clip) > 40 else ""),
                        }
                        self.r.publish(f"events:{self.session_id}", json.dumps(event_payload))
                except Exception:
                    pass
                time.sleep(0.8)

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

    # --- Heartbeat Loop ---

    def run_heartbeat_loop(self):
        while self.running:
            try:
                self.r.set(f"desktop:{self.session_id}:alive", "1", ex=25)
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

    print("[DeskAgent] Desktop agent running successfully.")
    agent.run_heartbeat_loop()


if __name__ == "__main__":
    main()
