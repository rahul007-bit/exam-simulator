import subprocess
import threading
import time
from typing import List, Optional

from core.desktop_manager import desktop_mgr
from core.redis_bus import bus as redis_bus, get_system_resource_info

_running_containers_cache: set = set()
_last_container_cache_time: float = 0.0


def get_running_desktop_containers() -> set:
    """Returns a cached set of running desktop container names with a 2-second TTL to avoid CLI subprocess storms."""
    global _running_containers_cache, _last_container_cache_time
    now = time.time()
    if now - _last_container_cache_time < 2.0 and _running_containers_cache is not None:
        return _running_containers_cache
    try:
        r = subprocess.run(
            ["docker", "ps", "--filter", "name=cka-desktop-", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode == 0:
            _running_containers_cache = set(r.stdout.strip().split())
            _last_container_cache_time = now
            return _running_containers_cache
    except Exception:
        pass
    return _running_containers_cache


def is_container_running(sid: Optional[str]) -> bool:
    """Checks whether the docker desktop container for the session is actively running (O(1) cached lookup)."""
    if not sid or sid == "None":
        return False
    container_name = f"cka-desktop-{sid}"
    running_set = get_running_desktop_containers()
    return container_name in running_set


_desktop_restore_inflight: set = set()
_desktop_restore_lock = threading.Lock()


def auto_restore_desktop(sid: Optional[str]) -> None:
    """Restores a missing desktop container only for a genuinely live session.

    Guards against:
    - stale state snapshots of submitted/terminated sessions;
    - the teardown race: a browser VNC auto-reconnect while
      teardown_session is deleting resources used to re-create the desktop
      mid-teardown. teardown now deregisters the session FIRST, and here we
      re-check liveness inside an in-flight lock so concurrent reconnects
      neither resurrect a dying session nor double-start the desktop.
    """
    if not sid:
        return
    with _desktop_restore_lock:
        if sid in _desktop_restore_inflight:
            return
        _desktop_restore_inflight.add(sid)
    try:
        if not redis_bus.is_session_active(sid):
            return
        state = redis_bus.get_session_state(sid) or {}
        if state.get("status", "active") != "active":
            return
        if is_container_running(sid):
            return
        res_info = get_system_resource_info()
        if res_info.get("available_mem_mb", 0) < 350:
            return
        print(f"[AutoRestore] Container for active session {sid} was not running. Automatically restored.", flush=True)
        desktop_mgr.start_desktop(sid)
    finally:
        with _desktop_restore_lock:
            _desktop_restore_inflight.discard(sid)


def _is_docker_container_active(cname: str) -> bool:
    """Direct live inspect to confirm container is running without caching delay."""
    try:
        r = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", cname],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return r.returncode == 0 and "true" in r.stdout.lower()
    except Exception:
        return False


def _find_running_desktop_containers() -> List[str]:
    """Finds all running cka-desktop-* container names."""
    try:
        r = subprocess.run(
            ["docker", "ps", "--filter", "name=cka-desktop-", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if r.returncode == 0 and r.stdout.strip():
            return [line.strip() for line in r.stdout.strip().splitlines() if line.strip()]
    except Exception:
        pass
    return []
