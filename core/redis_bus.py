import asyncio
import json
import os
import subprocess
import time
from typing import Any, Dict, Optional

try:
    import redis
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))


class RedisBus:
    def __init__(self, host: str = REDIS_HOST, port: int = REDIS_PORT, db: int = REDIS_DB):
        self.host = host
        self.port = port
        self.db = db
        self._sync_client: Optional[redis.Redis] = None
        self._bytes_client: Optional[redis.Redis] = None
        self._async_client: Optional[aioredis.Redis] = None
        self._is_connected = False

    def is_available(self) -> bool:
        """Returns True if Redis server is reachable."""
        if not HAS_REDIS:
            return False
        try:
            client = self.get_sync_client()
            return bool(client.ping())
        except Exception:
            return False

    def get_sync_client(self) -> redis.Redis:
        """Returns synchronous Redis client with string decoding."""
        if self._sync_client is None:
            self._sync_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                socket_timeout=2,
                socket_connect_timeout=2,
                decode_responses=True,
            )
        return self._sync_client

    def get_bytes_client(self) -> redis.Redis:
        """Returns synchronous Redis client for raw binary data (e.g. terminal pty stream)."""
        if self._bytes_client is None:
            self._bytes_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                socket_timeout=2,
                socket_connect_timeout=2,
                decode_responses=False,
            )
        return self._bytes_client

    def get_async_client(self) -> aioredis.Redis:
        """Returns asynchronous Redis client for FastAPI WebSockets."""
        if self._async_client is None:
            self._async_client = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                socket_timeout=2,
                socket_connect_timeout=2,
                decode_responses=True,
            )
        return self._async_client

    def publish_session_event(self, session_id: str, event_data: Dict[str, Any]) -> bool:
        """Synchronously publishes an event to session:{session_id} channel."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            payload = json.dumps(event_data)
            client.publish(f"session:{session_id}", payload)
            if session_id != "active":
                client.publish("session:active", payload)
            return True
        except Exception as e:
            print(f"[RedisBus] Failed to publish event: {e}")
            return False

    async def async_publish_session_event(self, session_id: str, event_data: Dict[str, Any]) -> bool:
        """Asynchronously publishes an event to session:{session_id} channel."""
        try:
            client = self.get_async_client()
            payload = json.dumps(event_data)
            await client.publish(f"session:{session_id}", payload)
            if session_id != "active":
                await client.publish("session:active", payload)
            return True
        except Exception as e:
            print(f"[RedisBus] Failed async publish: {e}")
            return False

    def set_clipboard(self, session_id: str, text: str) -> None:
        """Sets host clipboard selection and publishes to Redis."""
        # 1. Update host X11 selection for VNC
        env = {
            "DISPLAY": os.getenv("VNC_DISPLAY", ":1"),
            "XAUTHORITY": os.getenv("XAUTHORITY", "/home/exam/.Xauthority"),
            "HOME": os.getenv("EXAM_HOME", "/home/exam"),
        }
        try:
            subprocess.run(["xsel", "-b", "-i"], input=text, text=True, env=env, timeout=1)
            subprocess.run(["xsel", "-p", "-i"], input=text, text=True, env=env, timeout=1)
        except Exception:
            pass

        # 2. Store in Redis and publish
        if self.is_available():
            try:
                client = self.get_sync_client()
                client.set(f"clipboard:{session_id}", text, ex=3600)
                client.set("clipboard:active", text, ex=3600)
                payload = json.dumps({
                    "type": "clipboard_update",
                    "text": text,
                    "timestamp": time.time(),
                })
                client.publish(f"clipboard:{session_id}", payload)
                if session_id != "active":
                    client.publish("clipboard:active", payload)
                self.publish_session_event(session_id, {
                    "type": "clipboard_update",
                    "text": text,
                    "timestamp": time.time(),
                })
            except Exception:
                pass

    async def async_set_clipboard(self, session_id: str, text: str) -> None:
        """Asynchronously sets host clipboard selection and publishes to Redis."""
        # Run subprocess in executor to avoid blocking event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self.set_clipboard, session_id, text)

    def get_clipboard(self, session_id: str) -> str:
        """Retrieves current clipboard text from Redis cache or fallback to xsel."""
        if self.is_available():
            try:
                client = self.get_sync_client()
                val = client.get(f"clipboard:{session_id}")
                if val is not None:
                    return str(val)
            except Exception:
                pass

        env = {
            "DISPLAY": os.getenv("VNC_DISPLAY", ":1"),
            "XAUTHORITY": os.getenv("XAUTHORITY", "/home/exam/.Xauthority"),
            "HOME": os.getenv("EXAM_HOME", "/home/exam"),
        }
        try:
            res = subprocess.run(["xsel", "-b", "-o"], env=env, capture_output=True, text=True, timeout=1)
            text = res.stdout
            if not text:
                res_p = subprocess.run(["xsel", "-p", "-o"], env=env, capture_output=True, text=True, timeout=1)
                text = res_p.stdout
            return text or ""
        except Exception:
            return ""

    def register_active_session(self, session_id: str, session_meta: Dict[str, Any]) -> None:
        """Saves session metadata in Redis hash session:{session_id} and adds to active_sessions."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.hset(f"session:{session_id}", mapping={
                "session_id": session_id,
                "name": session_meta.get("name", "CKA Exam"),
                "total_tasks": str(session_meta.get("total_tasks", 0)),
                "start_timestamp": str(session_meta.get("start_timestamp", time.time())),
                "end_timestamp": str(session_meta.get("end_timestamp", time.time() + 7200)),
                "status": "active",
                "meta": json.dumps(session_meta),
            })
            client.sadd("active_sessions", session_id)
        except Exception as e:
            print(f"[RedisBus] Failed to register active session: {e}")

    def deregister_session(self, session_id: str) -> None:
        """Removes session from active_sessions and marks state completed."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.srem("active_sessions", session_id)
            client.hset(f"session:{session_id}", "status", "completed")
            client.expire(f"session:{session_id}", 86400)
            self.publish_session_event(session_id, {"type": "session_terminated", "session_id": session_id})
        except Exception:
            pass

    # --- Terminal Output Buffer (Scrollback Replay on Reconnect) ---

    def append_terminal_buffer(self, session_id: str, data: bytes, max_chunks: int = 200) -> None:
        """Appends output chunk to session terminal ring buffer."""
        if not self.is_available() or not data:
            return
        try:
            client = self.get_bytes_client()
            key = f"terminal:buffer:{session_id}"
            client.rpush(key, data)
            client.ltrim(key, -max_chunks, -1)
            client.expire(key, 7200)
        except Exception:
            pass

    def get_terminal_buffer(self, session_id: str) -> list[bytes]:
        """Retrieves terminal scrollback buffer for session reconnect."""
        if not self.is_available():
            return []
        try:
            client = self.get_bytes_client()
            key = f"terminal:buffer:{session_id}"
            return client.lrange(key, 0, -1) or []
        except Exception:
            return []

    def clear_terminal_buffer(self, session_id: str) -> None:
        """Clears terminal buffer for session."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.delete(f"terminal:buffer:{session_id}")
        except Exception:
            pass

    # --- In-Memory Session State Storage ---

    def set_session_state(self, session_id: str, state_dict: Dict[str, Any]) -> bool:
        """Stores active session state in Redis."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            client.set(f"session:{session_id}", json.dumps(state_dict), ex=86400)
            client.set("session:active:id", session_id, ex=86400)
            return True
        except Exception:
            return False

    def get_session_state(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves session state from Redis."""
        if not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            sid = session_id or client.get("session:active:id")
            if not sid:
                return None
            raw = client.get(f"session:{sid}")
            if raw:
                return json.loads(raw)
            return None
        except Exception:
            return None

    def clear_session_state(self, session_id: Optional[str] = None) -> None:
        """Clears session state and terminal buffer from Redis."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            sid = session_id or client.get("session:active:id")
            if sid:
                client.delete(f"session:{sid}")
                client.delete(f"clipboard:{sid}")
                client.delete(f"terminal:buffer:{sid}")
                client.delete(f"desktop:{sid}")
            client.delete("session:active:id")
        except Exception:
            pass

    # --- Desktop Registration & Dynamic Ingress ---

    def set_desktop_info(self, session_id: str, host: str, vnc_port: int = 5901, ws_port: int = 6080, container_id: str = "") -> bool:
        """Stores desktop endpoint info for dynamic routing."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            data = {
                "host": host,
                "vnc_port": str(vnc_port),
                "ws_port": str(ws_port),
                "container_id": container_id,
            }
            client.hset(f"desktop:{session_id}", mapping=data)
            client.expire(f"desktop:{session_id}", 86400)
            return True
        except Exception:
            return False

    def get_desktop_info(self, session_id: str) -> Optional[Dict[str, str]]:
        """Retrieves desktop endpoint info from Redis."""
        if not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            data = client.hgetall(f"desktop:{session_id}")
            if data:
                return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in data.items()}
            return None
        except Exception:
            return None

    def clear_desktop_info(self, session_id: str) -> None:
        """Removes desktop routing info from Redis."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.delete(f"desktop:{session_id}")
        except Exception:
            pass


# Global singleton instance
bus = RedisBus()
