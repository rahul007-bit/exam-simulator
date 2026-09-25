# --- Background Workers: Host Clipboard, Timer Broadcast, Idle Reaper, Timer Expiry ---

import asyncio
import os
import subprocess
import time
from pathlib import Path

from core.redis_bus import bus as redis_bus
from core.sandbox_orchestrator import orchestrator
from web.api.clipboard_state import get_x11_clipboard, set_x11_clipboard
from web.api.exam_helpers import _calculate_time_remaining
from web.api.state import IDLE_TIMEOUT_MINUTES, deployer, loader


async def start_background_workers():
    # 1. Initial scan: warm up question catalog and kubectl completion in Redis
    loop = asyncio.get_running_loop()
    def warm_up_cache():
        try:
            print("[Startup] Scanning question catalog into Redis...", flush=True)
            loader.reload(use_cache=False)
            count = len(loader.all())
            print(f"[Startup] Question catalog pre-warmed: {count} questions cached in Redis.", flush=True)
        except Exception as ex:
            print(f"[Startup] Catalog cache warm-up error: {ex}", flush=True)

        # Pre-cache kubectl completion in Redis and write to /etc/bash_completion.d/kubectl
        try:
            comp = redis_bus.get_kubectl_completion()
            if not comp:
                r = subprocess.run(["kubectl", "completion", "bash"], capture_output=True, text=True, timeout=10)
                if r.returncode == 0 and r.stdout:
                    comp = r.stdout
                    redis_bus.cache_kubectl_completion(comp)
            if comp:
                p = Path("/etc/bash_completion.d/kubectl")
                if not p.exists() or p.stat().st_size == 0:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(comp, encoding="utf-8")
        except Exception:
            pass

    async def _run_warmup():
        await loop.run_in_executor(None, warm_up_cache)

    asyncio.create_task(_run_warmup())

    asyncio.create_task(_clipboard_x11_monitor())
    asyncio.create_task(_session_timer_broadcaster())
    asyncio.create_task(_idle_session_reaper())
    asyncio.create_task(_session_expiry_enforcer())


async def _clipboard_x11_monitor():
    loop = asyncio.get_running_loop()
    while True:
        try:
            session = deployer.load_active_session(loader)
            if session and session.session_id:
                sid = session.session_id
                def read_xsel():
                    env = {
                        "DISPLAY": os.getenv("VNC_DISPLAY", ":1"),
                        "XAUTHORITY": os.getenv("XAUTHORITY", "/home/exam/.Xauthority"),
                        "HOME": os.getenv("EXAM_HOME", "/home/exam"),
                    }
                    try:
                        res = subprocess.run(["xsel", "-b", "-o"], env=env, capture_output=True, text=True, timeout=1)
                        t = res.stdout
                        if not t:
                            res_p = subprocess.run(["xsel", "-p", "-o"], env=env, capture_output=True, text=True, timeout=1)
                            t = res_p.stdout
                        return t or ""
                    except Exception:
                        return ""

                current = await loop.run_in_executor(None, read_xsel)
                if current and current != get_x11_clipboard():
                    set_x11_clipboard(current)
                    await redis_bus.async_publish_session_event(sid, {
                        "type": "clipboard_update",
                        "text": current,
                        "timestamp": time.time(),
                    })
        except Exception:
            pass
        await asyncio.sleep(1.0)

async def _session_timer_broadcaster():
    while True:
        try:
            for sid in redis_bus.list_active_session_ids():
                session = deployer.load_session(loader, sid)
                if not session or not session.session_id:
                    continue
                rem = _calculate_time_remaining(session)
                if rem is not None:
                    await redis_bus.async_publish_session_event(session.session_id, {
                        "type": "timer_tick",
                        "time_remaining_seconds": rem,
                        "server_timestamp": time.time(),
                    })
        except Exception:
            pass
        await asyncio.sleep(2.0)
async def _idle_session_reaper():
    """Auto-terminates any live session idle for IDLE_TIMEOUT_MINUTES with no activity."""
    while True:
        await asyncio.sleep(30)  # Check every minute

        # Orphan sweep: an id registered in active_sessions without a live
        # session record (e.g. session:key expired after 24h TTL) can never be
        # loaded — the loop below `continue`s over it forever, so its k3d
        # cluster and desktop container leak indefinitely. The session record
        # lives in Redis under session:{sid}; archive history lives under
        # history:session:{sid}. Anything with neither is unownable.
        try:
            client = redis_bus.get_sync_client()
            orphans = [
                sid
                for sid in redis_bus.list_active_session_ids()
                if not client.exists(f"session:{sid}", f"history:session:{sid}")
            ]
        except Exception:
            orphans = []
        if orphans:
            print(f"[OrphanSweep] Reclaiming sessions with no record: {orphans}", flush=True)
            loop = asyncio.get_running_loop()
            # teardown_session deregisters + cleans the Redis keys itself.
            def _teardown_all(ids):
                for sid in ids:
                    try:
                        orchestrator.teardown_session(sid)
                    except Exception as ex:
                        print(f"[OrphanSweep] teardown {sid} failed: {ex}", flush=True)
            await loop.run_in_executor(None, _teardown_all, list(orphans))

        try:
            for sid in redis_bus.list_active_session_ids():
                session = deployer.load_session(loader, sid)
                if not session or not session.session_id:
                    continue

                last_active = redis_bus.get_session_last_active(session.session_id)
                if last_active is None:
                    # No activity record yet; seed it now
                    redis_bus.touch_session_activity(session.session_id)
                    continue

                idle_seconds = time.time() - last_active
                idle_limit_seconds = IDLE_TIMEOUT_MINUTES * 60
                if idle_seconds >= idle_limit_seconds:
                    print(
                        f"[SessionReaper] Session {session.session_id} idle for "
                        f"{int(idle_seconds)}s (limit {idle_limit_seconds}s). Terminating."
                    )
                    try:
                        await redis_bus.async_publish_session_event(session.session_id, {
                            "type": "session_expired",
                            "reason": "idle_timeout",
                            "idle_seconds": int(idle_seconds),
                            "message": f"Session expired due to {IDLE_TIMEOUT_MINUTES} minutes of inactivity.",
                        })
                    except Exception:
                        pass
                    await asyncio.sleep(2)  # Give WS clients time to receive the event
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, lambda sid=session.session_id: (
                        redis_bus.archive_session(sid, status="idle_timeout"),
                        orchestrator.teardown_session(sid),
                        deployer.clear_active_session(sid),
                    ))
        except Exception as e:
            print(f"[SessionReaper] Error: {e}")


async def _session_expiry_enforcer():
    """Server-side enforcement: terminates any live session when its time hits zero."""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds
        try:
            for sid in redis_bus.list_active_session_ids():
                session = deployer.load_session(loader, sid)
                if not session or not session.session_id:
                    continue
                if not session.time_limit_minutes:
                    continue  # Untimed session

                rem = _calculate_time_remaining(session)
                if rem is not None and rem <= 0:
                    print(
                        f"[ExpiryEnforcer] Session {session.session_id} time limit reached. Auto-submitting."
                    )
                    try:
                        await redis_bus.async_publish_session_event(session.session_id, {
                            "type": "session_expired",
                            "reason": "time_limit",
                            "message": "Exam time limit reached. Session auto-submitted.",
                        })
                    except Exception:
                        pass
                    await asyncio.sleep(2)
                    # Archive as expired (not graded since we don't have full grading context async)
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(None, lambda sid=session.session_id: (
                        redis_bus.archive_session(sid, status="expired"),
                        orchestrator.teardown_session(sid),
                        deployer.clear_active_session(sid),
                    ))
        except Exception as e:
            print(f"[ExpiryEnforcer] Error: {e}")
