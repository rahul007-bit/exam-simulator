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
        """Returns synchronous Redis client."""
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
            channel = f"session:{session_id}"
            client.publish(channel, json.dumps(event_data))
            return True
        except Exception as e:
            print(f"[RedisBus] Failed to publish event: {e}")
            return False

    async def async_publish_session_event(self, session_id: str, event_data: Dict[str, Any]) -> bool:
        """Asynchronously publishes an event to session:{session_id} channel."""
        try:
            client = self.get_async_client()
            channel = f"session:{session_id}"
            await client.publish(channel, json.dumps(event_data))
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


# Global singleton instance
bus = RedisBus()
