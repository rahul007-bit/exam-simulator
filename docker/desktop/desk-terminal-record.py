#!/usr/bin/env python3
"""
Desktop terminal recorder wrapper.

Replaces the plain shell inside the in-desktop terminal (xfce4-terminal). It
runs the candidate shell under a local pty, forwards I/O to the visible terminal,
and publishes every output chunk / input keystroke to the session event channel
as the `user-desktop` channel (actor `user`). The recorder subscribes and writes
these into the `{session_id}.user-desktop.cast` asciinema stream, so the desktop
terminal is fully replayable (input + output).

Environment: SESSION_ID, REDIS_HOST, REDIS_PORT (defaults for local dev).
"""
import json
import os
import pty
import select
import shutil
import signal
import struct
import sys
import termios
import time
import tty

SESSION_ID = os.getenv("SESSION_ID", "default")
REDIS_HOST = os.getenv("REDIS_HOST", "172.17.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

try:
    import redis  # type: ignore

    _client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_timeout=2)
except Exception:  # pragma: no cover - degrade when redis is unavailable
    _client = None

_CHANNEL = "user-desktop"


def _publish(payload: dict) -> None:
    if _client is None:
        return
    try:
        _client.publish(f"events:{SESSION_ID}", json.dumps(payload))
    except Exception:
        pass


def _set_winsize(fd: int, rows: int, cols: int) -> None:
    try:
        import fcntl

        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
    except Exception:
        pass


def main() -> int:
    shell = os.environ.get("SHELL", "/bin/bash")
    cols, rows = shutil.get_terminal_size((120, 34))

    pid, master_fd = pty.fork()
    if pid == 0:
        os.environ["TERM"] = "xterm-256color"
        os.environ["COLORTERM"] = "truecolor"
        try:
            os.execvp(shell, [shell, "-l"])
        except Exception:
            os._exit(127)

    _set_winsize(master_fd, rows, cols)

    stdin_fd = sys.stdin.fileno()
    stdout_fd = sys.stdout.fileno()
    old_attrs = None
    try:
        old_attrs = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)
    except Exception:
        old_attrs = None

    def _on_resize(signum, frame):
        c, r = shutil.get_terminal_size((cols, rows))
        _set_winsize(master_fd, r, c)

    try:
        signal.signal(signal.SIGWINCH, _on_resize)
    except Exception:
        pass

    try:
        while True:
            try:
                ready, _, _ = select.select([master_fd, stdin_fd], [], [], 0.2)
            except Exception:
                break

            if master_fd in ready:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                try:
                    os.write(stdout_fd, data)
                except Exception:
                    pass
                _publish({
                    "event": "DESKTOP_TERMINAL_OUTPUT",
                    "data": data.decode("utf-8", "replace"),
                    "channel": _CHANNEL,
                    "actor": "user",
                    "timestamp": time.time(),
                })

            if stdin_fd in ready:
                try:
                    data = os.read(stdin_fd, 1024)
                except OSError:
                    break
                if not data:
                    break
                try:
                    os.write(master_fd, data)
                except Exception:
                    pass
                _publish({
                    "event": "DESKTOP_TERMINAL_INPUT",
                    "text": data.decode("utf-8", "replace"),
                    "channel": _CHANNEL,
                    "actor": "user",
                    "timestamp": time.time(),
                })
    finally:
        if old_attrs is not None:
            try:
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_attrs)
            except Exception:
                pass
        try:
            os.close(master_fd)
        except Exception:
            pass
        try:
            os.kill(pid, signal.SIGHUP)
            os.waitpid(pid, 0)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
