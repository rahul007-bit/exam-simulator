# --- Built-in WebSocket PTY Terminal ---

import fcntl
import json
import os
import pty
import select
import struct
import sys
import termios
import asyncio
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.recorder import recorder
from core.redis_bus import bus as redis_bus
from web.api.desktop_restore import _is_docker_container_active
from web.api.owner_lock import _client_id_ws, _owner_mismatch
from web.api.security import is_admin_authenticated

router = APIRouter()


@router.websocket("/ws/terminal")
@router.websocket("/ws/terminal/{session_id}")
async def terminal_websocket(websocket: WebSocket, session_id: Optional[str] = None):
    await websocket.accept()

    is_admin = is_admin_authenticated(websocket)
    actor = "admin" if is_admin else "candidate"
    channel = "admin-web" if is_admin else "user-web"
    param_sid = session_id or websocket.query_params.get("session_id")
    explicit_sid: Optional[str] = param_sid if (param_sid and param_sid not in ("default", "active")) else None

    # Resolve target container & session ID cleanly (never fall back to host shell)
    target_container: Optional[str] = None
    sid: Optional[str] = None

    # Admins must attach explicitly: a stale admin terminal tab must never
    # auto-follow whatever session becomes active next (that injected stray
    # ADMIN_TERMINAL_* events into unrelated candidate sessions).
    if is_admin and not explicit_sid:
        try:
            await websocket.send_bytes(
                b"\r\n\x1b[33m[Admin] Explicit session required: use /ws/terminal/<session_id>.\x1b[0m\r\n"
            )
            await asyncio.sleep(1)
            await websocket.close(code=1008)
        except Exception:
            pass
        return

    # Candidates may only attach to their own live session (FS-003b: the
    # requested sid must be a registered active session owned by this client;
    # there is no global-active fallback).
    if not is_admin:
        target_sid = explicit_sid
        if not target_sid or not redis_bus.is_session_active(target_sid):
            print(f"[Terminal] Forbidden: candidate attempted to access session {param_sid}", flush=True)
            await websocket.close(code=1008)
            return
        if _owner_mismatch(target_sid, _client_id_ws(websocket), False):
            print(f"[Terminal] Forbidden: session {target_sid} owned by another client", flush=True)
            await websocket.close(code=1008, reason="Session active in another window or device")
            return
        explicit_sid = target_sid

    # Wait up to 12 seconds for the requested session's container — and never
    # fall through to a different session (explicit requests must not silently
    # attach elsewhere when their container is gone).
    for attempt in range(24):
        cname = f"cka-desktop-{explicit_sid}"
        if _is_docker_container_active(cname):
            target_container = cname
            sid = explicit_sid
            break

        # If not ready on first try, show waiting banner to terminal
        if attempt == 0:
            try:
                await websocket.send_bytes(
                    b"\r\n\x1b[33m[Simulator] Waiting for exam container to become ready...\x1b[0m\r\n"
                )
            except Exception:
                pass

        await asyncio.sleep(0.5)

    if not target_container or not sid:
        try:
            await websocket.send_bytes(
                b"\r\n\x1b[31m[Error] Exam container is not running or ready.\r\nPlease start an exam session from the dashboard or wait for the environment to finish loading.\x1b[0m\r\n"
            )
            await asyncio.sleep(1)
            await websocket.close(code=1008)
        except Exception:
            pass
        return

    try:
        recorder.attach_or_resume(sid)
        recorder.log_event(
            "ADMIN_TERMINAL_ATTACH" if is_admin else "TERMINAL_ATTACH",
            {"session_id": sid, "container": target_container, "actor": actor},
            actor=actor,
            channel=channel,
        )
    except Exception:
        pass

    # Instant scrollback replay — only for the candidate's own channel. The
    # admin terminal is a fresh shell with NO candidate history and no buffer.
    if channel == "user-web":
        try:
            buffered_chunks = redis_bus.get_terminal_buffer(sid, channel)
            for chunk in buffered_chunks:
                await websocket.send_bytes(chunk)
        except Exception:
            pass

    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["COLORTERM"] = "truecolor"
    env["EXAM_RECORDED"] = "1"
    env["WEB_TERMINAL"] = "1"

    pid, master_fd = pty.fork()
    if pid == 0:
        try:
            os.setpgid(0, 0)
            termios.tcsetpgrp(0, os.getpgrp())
        except Exception:
            pass
        docker_cmd = [
            "docker", "exec", "-it",
            "-u", "exam",
            "-e", "TERM=xterm-256color",
            "-e", "COLORTERM=truecolor",
            "-e", "EXAM_RECORDED=1",
            "-e", "WEB_TERMINAL=1",
            target_container,
            "bash", "-l",
        ]
        try:
            os.execvp("docker", docker_cmd)
        except Exception as e:
            sys.stderr.write(f"\r\n\x1b[31m[Error] Failed to exec container '{target_container}': {e}\x1b[0m\r\n")
            sys.stderr.flush()
            sys.exit(1)
    else:
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        async def read_from_pty():
            while True:
                try:
                    await asyncio.sleep(0.01)
                    r, _, _ = select.select([master_fd], [], [], 0)
                    if r:
                        data = os.read(master_fd, 4096)
                        if not data:
                            break
                        try:
                            recorder.record_output(data, channel=channel)
                        except Exception:
                            pass
                        try:
                            if channel == "user-web":
                                redis_bus.append_terminal_buffer(sid, data, channel=channel)
                        except Exception:
                            pass
                        await websocket.send_bytes(data)
                except Exception:
                    break

        async def write_to_pty():
            while True:
                try:
                    msg = await websocket.receive()
                    if "bytes" in msg and msg["bytes"]:
                        os.write(master_fd, msg["bytes"])
                        try:
                            recorder.record_input(msg["bytes"], actor=actor, channel=channel)
                        except Exception:
                            pass
                    elif "text" in msg and msg["text"]:
                        text = msg["text"]
                        if text.startswith('{"resize":'):
                            try:
                                rdata = json.loads(text)["resize"]
                                rows = int(rdata.get("rows", 24))
                                cols = int(rdata.get("cols", 80))
                                winsize = struct.pack("HHHH", rows, cols, 0, 0)
                                fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                                recorder.record_resize(cols, rows, channel=channel)
                            except Exception:
                                pass
                        else:
                            raw_b = text.encode("utf-8")
                            os.write(master_fd, raw_b)
                            try:
                                recorder.record_input(raw_b, actor=actor, channel=channel)
                            except Exception:
                                pass
                except WebSocketDisconnect:
                    break
                except Exception:
                    break

        read_task = asyncio.create_task(read_from_pty())
        write_task = asyncio.create_task(write_to_pty())

        done, pending = await asyncio.wait(
            [read_task, write_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)


        try:
            recorder.flush_input_buffer(actor)
            recorder.log_event("ADMIN_TERMINAL_DETACH" if is_admin else "TERMINAL_DETACH", {"session_id": sid, "actor": actor}, actor=actor, channel=channel)
            if channel == "user-web":
                redis_bus.expire_terminal_buffer(sid, channel, 300)
        except Exception:
            pass

        try:
            os.close(master_fd)
            os.kill(pid, 9)
            os.waitpid(pid, 0)
        except Exception:
            pass
