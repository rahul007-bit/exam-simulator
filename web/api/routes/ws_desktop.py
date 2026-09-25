# --- Integrated noVNC WebSocket Proxy ---

import asyncio
import subprocess
from typing import Optional

from fastapi import APIRouter, WebSocket

from core.redis_bus import bus as redis_bus
from web.api.desktop_restore import _find_running_desktop_containers, auto_restore_desktop
from web.api.owner_lock import _client_id_ws, _owner_mismatch
from web.api.security import is_admin_authenticated
from web.api.state import deployer, loader

router = APIRouter()


async def _proxy_vnc(websocket: WebSocket, session_id: Optional[str] = None):
    requested_proto = websocket.headers.get("sec-websocket-protocol", "")
    subprotocol = "binary" if "binary" in requested_proto else None
    await websocket.accept(subprotocol=subprotocol)

    is_admin_mode = is_admin_authenticated(websocket)

    sid = session_id
    if not sid or sid in ("active", "default"):
        # FS-003b: only admins may fall back to the legacy most-recent session;
        # candidates must connect with their explicit session id.
        if is_admin_mode:
            active_sid = redis_bus.get_active_session_id()
            if active_sid:
                sid = active_sid
            else:
                s = deployer.load_active_session(loader)
                if s and s.session_id:
                    sid = s.session_id
                else:
                    running = _find_running_desktop_containers()
                    if running:
                        sid = running[0].replace("cka-desktop-", "")

    # Security check: candidates can ONLY access their own live session
    if not is_admin_mode:
        if not sid or not redis_bus.is_session_active(sid):
            print(f"[VNC Proxy] Forbidden: Candidate attempted to access unauthorized session {session_id}", flush=True)
            await websocket.close(code=1008)
            return
        if _owner_mismatch(sid, _client_id_ws(websocket), False):
            print(f"[VNC Proxy] Forbidden: session {sid} owned by another client", flush=True)
            await websocket.close(code=1008, reason="Session active in another window or device")
            return

    target_host = None
    target_port = 5901

    if sid:
        # Auto-Restore Container for Active Sessions (only when the session is
        # genuinely registered as active — never resurrect terminated ones).
        auto_restore_desktop(sid)

        # Check Redis registration, wait up to 10s if container is currently registering
        for _ in range(20):
            desktop_info = redis_bus.get_desktop_info(sid)
            if desktop_info and "host" in desktop_info:
                h = desktop_info["host"]
                # Reject 127.0.0.1 / localhost (container desktop only)
                if h not in ("127.0.0.1", "localhost"):
                    target_host = h
                    target_port = int(desktop_info.get("vnc_port", 5901))
                    break

            # Try docker inspect directly for the container IP if not in Redis yet
            try:
                ip_r = subprocess.run(
                    ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", f"cka-desktop-{sid}"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                cip = ip_r.stdout.strip()
                if cip:
                    target_host = cip
                    target_port = 5901
                    redis_bus.set_desktop_info(sid, host=cip, vnc_port=5901, ws_port=6080)
                    break
            except Exception:
                pass
            await asyncio.sleep(0.5)

    if not target_host or target_host in ("127.0.0.1", "localhost"):
        print(f"[VNC Proxy] Session {sid} has no running desktop container. Refusing VNC connection.", flush=True)
        await websocket.close(code=1008)
        return


    try:
        reader, writer = await asyncio.open_connection(target_host, target_port)
        print(f"[VNC Proxy] Connected to VNC at {target_host}:{target_port} (session: {session_id or 'default'}, resolved_sid: {sid})", flush=True)
    except Exception as e:
        print(f"[VNC Proxy] Failed to connect to VNC target {target_host}:{target_port}: {e}", flush=True)
        await websocket.close()
        return

    async def client_to_vnc():
        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if "bytes" in msg and msg["bytes"]:
                    writer.write(msg["bytes"])
                    await writer.drain()
                elif "text" in msg and msg["text"]:
                    writer.write(msg["text"].encode("latin1"))
                    await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def vnc_to_client():
        try:
            while True:
                data = await reader.read(16384)
                if not data:
                    break
                await websocket.send_bytes(data)
        except Exception:
            pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    c2v = asyncio.create_task(client_to_vnc())
    v2c = asyncio.create_task(vnc_to_client())

    done, pending = await asyncio.wait(
        [c2v, v2c],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)


    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


@router.websocket("/ws/desktop/{session_id}")
@router.websocket("/novnc/ws/desktop/{session_id}")
async def vnc_ws_dynamic_desktop(websocket: WebSocket, session_id: str):
    await _proxy_vnc(websocket, session_id=session_id)


@router.websocket("/ws/desktop")
@router.websocket("/novnc/ws/desktop")
async def vnc_ws_dynamic_desktop_default(websocket: WebSocket):
    await _proxy_vnc(websocket, session_id=None)


@router.websocket("/ws/vnc")
async def vnc_ws_primary(websocket: WebSocket):
    await _proxy_vnc(websocket)


@router.websocket("/websockify")
async def vnc_ws_websockify(websocket: WebSocket):
    await _proxy_vnc(websocket)


@router.websocket("/novnc/websockify")
async def vnc_ws_novnc_websockify(websocket: WebSocket):
    await _proxy_vnc(websocket)


@router.websocket("/novnc/ws/vnc")
async def vnc_ws_novnc_vnc(websocket: WebSocket):
    await _proxy_vnc(websocket)
