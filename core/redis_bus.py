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
        """Adds session_id to active_sessions set."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.sadd("active_sessions", session_id)
        except Exception as e:
            print(f"[RedisBus] Failed to register active session: {e}")

    def deregister_session(self, session_id: str) -> None:
        """Removes session from active_sessions."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.srem("active_sessions", session_id)
            active_id = client.get("session:active:id")
            if isinstance(active_id, bytes):
                active_id = active_id.decode()
            if active_id == session_id:
                client.delete("session:active:id")
            self.publish_session_event(session_id, {"type": "session_terminated", "session_id": session_id})
        except Exception:
            pass

    def is_session_active(self, session_id: str) -> bool:
        """True only when the session is the genuinely registered active one.

        Guards auto-restore paths against stale state snapshots: after
        submit/terminate the session must be considered dead even if an old
        state blob (status "active") is still cached in Redis.
        """
        if not self.is_available() or not session_id:
            return False
        try:
            client = self.get_sync_client()
            if not client.sismember("active_sessions", session_id):
                return False
            active_id = client.get("session:active:id")
            if isinstance(active_id, bytes):
                active_id = active_id.decode()
            return active_id == session_id
        except Exception:
            return False

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
            if isinstance(sid, bytes):
                sid = sid.decode()
            if not sid:
                return None
            raw = client.get(f"session:{sid}")

            if raw:
                return json.loads(raw)
            return None
        except Exception:
            return None

    def get_active_session_id(self) -> Optional[str]:
        """Returns the current active session ID from Redis if set."""
        if not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            sid = client.get("session:active:id")
            if isinstance(sid, bytes):
                return sid.decode()
            return sid
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
    def touch_session_activity(self, session_id: str) -> None:
        """Updates the last-activity timestamp for idle timeout tracking."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.set(f"session:{session_id}:last_active", str(time.time()), ex=86400)
        except Exception:
            pass

    def get_session_last_active(self, session_id: str) -> Optional[float]:
        """Returns Unix timestamp of last activity, or None."""
        if not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            val = client.get(f"session:{session_id}:last_active")
            return float(val) if val else None
        except Exception:
            return None

    def archive_session(self, session_id: str, status: str = "completed", scorecard: Optional[Dict] = None) -> None:
        """Moves session into the history archive in Redis (preserves for history list)."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            existing = client.get(f"session:{session_id}")
            meta: Dict[str, Any] = {}
            if existing:
                try:
                    meta = json.loads(existing)
                except Exception:
                    pass
            meta["status"] = status
            meta["archived_at"] = time.time()
            if scorecard:
                meta["scorecard_summary"] = scorecard
            # Write to history hash; keep for 30 days
            client.set(f"history:{session_id}", json.dumps(meta), ex=86400 * 30)
            client.zadd("session_history", {session_id: time.time()})
            # Clean up active tracking keys
            for suffix in ["", ":last_active", ":kubeconfig", ":exam_md"]:
                client.delete(f"session:{session_id}{suffix}")
            client.delete(f"desktop:{session_id}")
            client.delete(f"clipboard:{session_id}")
            client.delete(f"terminal:buffer:{session_id}")
            # Remove from active id pointer if it matches
            active_id = client.get("session:active:id")
            if isinstance(active_id, bytes):
                active_id = active_id.decode()
            if active_id == session_id or not active_id:
                client.delete("session:active:id")

        except Exception as e:
            print(f"[RedisBus] archive_session error: {e}")

    def list_session_history(self, limit: int = 50) -> list:
        """Returns list of recent sessions from history (newest first)."""
        if not self.is_available():
            return []
        try:
            client = self.get_sync_client()
            # Get recent session IDs sorted by archive time (newest first)
            ids = client.zrevrange("session_history", 0, limit - 1)
            result = []
            for sid in ids:
                raw = client.get(f"history:{sid}")
                if raw:
                    try:
                        data = json.loads(raw)
                        result.append({
                            "session_id": sid,
                            "name": data.get("name", "Unknown"),
                            "status": data.get("status", "unknown"),
                            "created_at": data.get("created_at", ""),
                            "archived_at": data.get("archived_at"),
                            "total_tasks": data.get("total_tasks", 0) or len(data.get("question_ids", [])),
                            "time_limit_minutes": data.get("time_limit_minutes"),
                            "scorecard_summary": data.get("scorecard_summary"),
                        })
                    except Exception:
                        pass
            return result
        except Exception:
            return []

    # --- Admin Auth, Config & Candidate Invitations ---

    def get_default_preset(self) -> str:
        """Retrieves global default preset name."""
        if self.is_available():
            try:
                client = self.get_sync_client()
                val = client.get("config:default_preset")
                if val:
                    return str(val)
            except Exception:
                pass
        return "mock-01-acme"

    def set_default_preset(self, preset: str) -> bool:
        """Sets global default preset name in Redis."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            client.set("config:default_preset", preset)
            return True
        except Exception:
            return False

    def store_admin_token(self, token: str, expires_in: int = 86400 * 7) -> bool:
        """Stores admin session token in Redis."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            client.set(f"admin:token:{token}", "1", ex=expires_in)
            return True
        except Exception:
            return False

    def verify_admin_token(self, token: str) -> bool:
        """Checks if admin session token is valid."""
        if not token or not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            val = client.get(f"admin:token:{token}")
            return bool(val)
        except Exception:
            return False

    def revoke_admin_token(self, token: str) -> None:
        """Invalidates admin session token."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.delete(f"admin:token:{token}")
        except Exception:
            pass

    def create_invitation(self, token: str, preset: str) -> Dict[str, Any]:
        """Creates a candidate invitation record in Redis."""
        data = {
            "token": token,
            "preset": preset,
            "created_at": time.time(),
            "status": "pending",
        }
        if self.is_available():
            try:
                client = self.get_sync_client()
                client.set(f"invitation:{token}", json.dumps(data), ex=86400 * 7)
                client.sadd("candidate_invitations", token)
            except Exception as e:
                print(f"[RedisBus] Failed to create invitation: {e}")
        return data

    def get_invitation(self, token: str) -> Optional[Dict[str, Any]]:
        """Retrieves invitation record for candidate token."""
        if not token or not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            raw = client.get(f"invitation:{token}")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return None

    def update_invitation(self, token: str, updates: Dict[str, Any]) -> bool:
        """Updates invitation record for candidate token."""
        if not token or not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            raw = client.get(f"invitation:{token}")
            if raw:
                data = json.loads(raw)
                data.update(updates)
                client.set(f"invitation:{token}", json.dumps(data), ex=86400 * 7)
                return True
        except Exception:
            pass
        return False

    def list_invitations(self) -> list:
        """Lists all invitations."""
        if not self.is_available():
            return []
        try:
            client = self.get_sync_client()
            tokens = client.smembers("candidate_invitations")
            res = []
            for t in tokens:
                token_str = t if isinstance(t, str) else t.decode()
                raw = client.get(f"invitation:{token_str}")
                if raw:
                    try:
                        res.append(json.loads(raw))
                    except Exception:
                        pass
                else:
                    client.srem("candidate_invitations", token_str)
            return sorted(res, key=lambda x: x.get("created_at", 0), reverse=True)
        except Exception:
            return []

    def delete_invitation(self, token: str) -> None:
        """Deletes an invitation."""
        if not self.is_available():
            return
        try:
            client = self.get_sync_client()
            client.delete(f"invitation:{token}")
            client.srem("candidate_invitations", token)
        except Exception:
            pass

    def get_max_concurrent_sessions(self) -> int:
        """Retrieves maximum allowed concurrent desktop sessions (default: 1)."""
        if self.is_available():
            try:
                client = self.get_sync_client()
                val = client.get("config:max_concurrent_sessions")
                if val is not None:
                    return max(1, int(val))
            except Exception:
                pass
        return 1

    def set_max_concurrent_sessions(self, limit: int) -> bool:
        """Sets maximum allowed concurrent desktop sessions in Redis."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            client.set("config:max_concurrent_sessions", max(1, int(limit)))
            return True
        except Exception:
            return False

    def get_archived_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves archived session data from Redis history."""
        if not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            raw = client.get(f"history:{session_id}")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return None

    def cache_question_catalog(self, catalog: Dict[str, Any], ttl: int = 86400 * 7) -> bool:
        """Caches the full scanned question catalog into Redis as JSON."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            client.set("catalog:questions", json.dumps(catalog), ex=ttl)
            return True
        except Exception:
            return False

    def get_cached_question_catalog(self) -> Optional[Dict[str, Any]]:
        """Retrieves cached question catalog from Redis."""
        if not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            raw = client.get("catalog:questions")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return None

    def cache_kubectl_completion(self, completion_script: str, ttl: int = 86400 * 30) -> bool:
        """Caches pre-compiled kubectl bash completion script in Redis."""
        if not self.is_available():
            return False
        try:
            client = self.get_sync_client()
            client.set("cache:kubectl_completion", completion_script, ex=ttl)
            return True
        except Exception:
            return False

    def get_kubectl_completion(self) -> Optional[str]:
        """Retrieves cached kubectl bash completion script from Redis."""
        if not self.is_available():
            return None
        try:
            client = self.get_sync_client()
            raw = client.get("cache:kubectl_completion")
            if raw:
                return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
        except Exception:
            pass
        return None



# Global singleton instance
bus = RedisBus()


def get_system_resource_info() -> Dict[str, Any]:
    """Inspects host memory and active desktop containers to compute concurrency capacity."""
    total_mem_mb = 0
    available_mem_mb = 0
    free_mem_mb = 0
    try:
        import psutil
        vm = psutil.virtual_memory()
        total_mem_mb = int(vm.total / (1024 * 1024))
        available_mem_mb = int(vm.available / (1024 * 1024))
        free_mem_mb = int(vm.free / (1024 * 1024))
    except Exception:
        try:
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        k = parts[0].strip()
                        v = parts[1].strip().split()[0]
                        if k == "MemTotal":
                            total_mem_mb = int(v) // 1024
                        elif k == "MemAvailable":
                            available_mem_mb = int(v) // 1024
                        elif k == "MemFree":
                            free_mem_mb = int(v) // 1024
        except Exception:
            pass

    used_mem_mb = max(0, total_mem_mb - available_mem_mb)

    # Running desktop containers
    running_containers = 0
    try:
        res = subprocess.run(
            ["docker", "ps", "-q", "--filter", "name=cka-desktop-"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0 and res.stdout.strip():
            running_containers = len([c for c in res.stdout.strip().splitlines() if c.strip()])
    except Exception:
        pass

    # Read config:max_concurrent_sessions from Redis (default: 1)
    max_concurrent_sessions = bus.get_max_concurrent_sessions()

    # Reserve 2500 MB for Kubernetes cluster (control plane + worker nodes) and host OS overhead
    k8s_reserved_mb = 2500
    usable_candidate_ram = max(0, available_mem_mb - k8s_reserved_mb)
    # Each desktop container requires ~700 MB; cap safe recommendation between 1 and 4
    recommended_max = max(1, min(4, (usable_candidate_ram + running_containers * 650) // 750))

    can_start = True
    reason = "Resources available"
    if running_containers >= max_concurrent_sessions:
        can_start = False
        reason = f"Maximum concurrent sessions ({max_concurrent_sessions}) currently active ({running_containers} running)"
    elif available_mem_mb < 350:
        can_start = False
        reason = f"Low server memory ({available_mem_mb} MB available, minimum required is 350 MB)"

    return {
        "total_mem_mb": total_mem_mb,
        "available_mem_mb": available_mem_mb,
        "used_mem_mb": used_mem_mb,
        "free_mem_mb": free_mem_mb,
        "running_containers": running_containers,
        "max_concurrent_sessions": max_concurrent_sessions,
        "recommended_max": recommended_max,
        "can_start": can_start,
        "reason": reason,
    }
