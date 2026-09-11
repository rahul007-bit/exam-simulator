# --- Real-Time Session & Redis Pub/Sub WebSocket ---

import asyncio
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.recorder import recorder
from core.redis_bus import bus as redis_bus
from web.api.clipboard_state import set_x11_clipboard
from web.api.owner_lock import _client_id_ws, _owner_mismatch
from web.api.security import is_admin_authenticated
from web.api.state import deployer, loader

router = APIRouter()


@router.websocket("/ws/session/{session_id}")
async def session_events_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # Soft per-session owner lock: only the owning client may subscribe to the
    # live event stream of a session (admins always bypass). FS-003b: enforces
    # against the requested session id, not the global active pointer.
    is_admin = is_admin_authenticated(websocket)
    owner_sid = None if session_id in ("active", "default") else session_id
    if owner_sid and not redis_bus.is_session_active(owner_sid):
        await websocket.close(code=1008, reason="Session is not active")
        return
    if owner_sid and _owner_mismatch(owner_sid, _client_id_ws(websocket), is_admin):
        await websocket.close(code=1008, reason="Session active in another window or device")
        return

    if not redis_bus.is_available():
        # Fallback loop if Redis is temporarily offline
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "clipboard_copy":
                        text = msg.get("text", "")
                        set_x11_clipboard(text)
                        await redis_bus.async_set_clipboard(session_id, text)
                        try:
                            recorder.attach_or_resume(session_id)
                            recorder.log_event("CLIPBOARD_COPY", {
                                "length": len(text),
                                "preview": text[:120],
                            })
                        except Exception:
                            pass
                except Exception:
                    pass
        except WebSocketDisconnect:
            pass
        return

    async_redis = redis_bus.get_async_client()
    pubsub = async_redis.pubsub()
    channel = f"session:{session_id}"
    await pubsub.subscribe(channel)

    async def pubsub_to_ws():
        try:
            async for message in pubsub.listen():
                if message.get("type") == "message":
                    raw_data = message.get("data")
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8")
                    await websocket.send_text(raw_data)
        except Exception:
            pass

    async def ws_to_redis():
        try:
            while True:
                raw_text = await websocket.receive_text()
                try:
                    payload = json.loads(raw_text)
                    msg_type = payload.get("type")
                    if msg_type == "clipboard_copy":
                        text = payload.get("text", "")
                        set_x11_clipboard(text)
                        target_sid = session_id
                        if target_sid == "active":
                            session = deployer.load_active_session(loader)
                            target_sid = session.session_id if session else "default"
                        await redis_bus.async_set_clipboard(target_sid, text)
                        try:
                            recorder.attach_or_resume(target_sid)
                            recorder.log_event("CLIPBOARD_COPY", {
                                "length": len(text),
                                "preview": text[:120],
                            })
                        except Exception:
                            pass
                    elif msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong", "time": time.time()}))

                    # Touch activity for any message to reset idle timeout
                    try:
                        target = session_id
                        if target == "active":
                            s = deployer.load_active_session(loader)
                            target = s.session_id if s else "default"
                        redis_bus.touch_session_activity(target)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    t1 = asyncio.create_task(pubsub_to_ws())
    t2 = asyncio.create_task(ws_to_redis())
    try:
        done, pending = await asyncio.wait([t1, t2], return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)

    finally:
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception:
            pass
