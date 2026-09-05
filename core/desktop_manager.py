"""
Ephemeral Containerized Desktop Manager
Spawns, monitors, and terminates isolated candidate desktops via Docker and Redis.
"""

import os
import time
import shutil
import subprocess
from typing import Optional, Dict, Any
from core.redis_bus import bus as redis_bus


class DesktopManager:
    IMAGE_NAME = "cka-desktop:latest"

    def __init__(self):
        self._docker_path: Optional[str] = shutil.which("docker")

    def is_docker_available(self) -> bool:
        """Verifies Docker daemon is operational."""
        if not self._docker_path:
            return False
        try:
            res = subprocess.run(
                ["docker", "info"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def is_image_available(self) -> bool:
        """Checks if cka-desktop:latest image is built locally."""
        if not self.is_docker_available():
            return False
        try:
            res = subprocess.run(
                ["docker", "image", "inspect", self.IMAGE_NAME],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
            )
            return res.returncode == 0
        except Exception:
            return False

    def start_desktop(self, session_id: str, redis_host: str = "172.17.0.1") -> bool:
        """Spawns an ephemeral candidate desktop container."""
        if not self.is_docker_available() or not self.is_image_available():
            # Fallback to host VNC
            print(f"[DesktopManager] Container desktop unavailable, falling back to host VNC for session {session_id}")
            redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
            return True

        container_name = f"cka-desktop-{session_id}"
        # Ensure any old container is cleaned
        self.stop_desktop(session_id)

        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "-e", f"SESSION_ID={session_id}",
            "-e", f"REDIS_HOST={redis_host}",
            "-e", "REDIS_PORT=6379",
            "--network", "bridge",
            self.IMAGE_NAME,
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                print(f"[DesktopManager] docker run failed: {res.stderr.strip()}")
                redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
                return False

            cid = res.stdout.strip()[:12]
            print(f"[DesktopManager] Started container {container_name} ({cid}) for session {session_id}")

            # Wait up to 10s for desk-agent inside container to register in Redis
            deadline = time.time() + 10.0
            while time.time() < deadline:
                info = redis_bus.get_desktop_info(session_id)
                if info and "host" in info:
                    print(f"[DesktopManager] Desktop registered in Redis: {info}")
                    return True
                time.sleep(0.5)

            print(f"[DesktopManager] Timeout waiting for desktop agent registration. Falling back to host VNC.")
            redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
            return True

        except Exception as e:
            print(f"[DesktopManager] Exception starting container: {e}")
            redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
            return False

    def stop_desktop(self, session_id: str) -> None:
        """Terminates and removes desktop container and cleans Redis state."""
        container_name = f"cka-desktop-{session_id}"
        if self.is_docker_available():
            try:
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except Exception:
                pass
        redis_bus.clear_desktop_info(session_id)


desktop_mgr = DesktopManager()
