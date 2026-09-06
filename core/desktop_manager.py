"""
Ephemeral Containerized Desktop Manager
Spawns, monitors, and terminates isolated candidate desktops via Docker and Redis.
"""
import os
import time
import shutil
import subprocess
from pathlib import Path
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

    def _inject_kubeconfig(self, session_id: str, redis_host: str = "172.17.0.1") -> None:
        """Extracts host kubeconfig, patches localhost endpoints to container-accessible gateway, and caches in Redis."""
        kube_candidates = [
            Path("/home/exam/.kube/config"),
            Path(os.path.expanduser("~/.kube/config")),
            Path("/root/.kube/config"),
            Path("/etc/kubernetes/admin.conf"),
        ]
        kube_text = None
        for p in kube_candidates:
            if p.exists() and p.is_file():
                try:
                    content = p.read_text()
                    if content.strip():
                        kube_text = content
                        break
                except Exception:
                    pass

        if not kube_text:
            return

        # Rewrite 0.0.0.0 and 127.0.0.1 cluster URLs to host gateway IP with TLS skip
        try:
            import yaml
            doc = yaml.safe_load(kube_text)
            if isinstance(doc, dict):
                for cluster in doc.get("clusters", []):
                    c_info = cluster.get("cluster", {})
                    srv = c_info.get("server", "")
                    if "0.0.0.0" in srv or "127.0.0.1" in srv:
                        c_info["server"] = srv.replace("0.0.0.0", redis_host).replace("127.0.0.1", redis_host)
                        c_info.pop("certificate-authority-data", None)
                        c_info["insecure-skip-tls-verify"] = True
                kube_text = yaml.safe_dump(doc, sort_keys=False)
        except Exception:
            kube_text = kube_text.replace("https://0.0.0.0:", f"https://{redis_host}:")
            kube_text = kube_text.replace("https://127.0.0.1:", f"https://{redis_host}:")

        try:
            client = redis_bus.get_sync_client()
            if client:
                client.setex(f"session:{session_id}:kubeconfig", 86400, kube_text)
                client.setex("k8s:kubeconfig", 86400, kube_text)
                print(f"[DesktopManager] Injected cluster kubeconfig into Redis for session {session_id}")
        except Exception as ex:
            print(f"[DesktopManager] Warning: failed to store kubeconfig in Redis: {ex}")

    def start_desktop(self, session_id: str, redis_host: str = "172.17.0.1") -> bool:
        """Spawns an ephemeral candidate desktop container with full XFCE & kubectl."""
        is_admin = os.getenv("EXAM_ADMIN", "0").lower() in ("1", "true")
        if not self.is_docker_available() or not self.is_image_available():
            if is_admin:
                print(f"[DesktopManager] Container desktop unavailable, falling back to host VNC for admin session {session_id}")
                redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
                return True
            else:
                print(f"[DesktopManager] Error: Container desktop unavailable for candidate session {session_id} (host fallback disabled)")
                return False

        container_name = f"cka-desktop-{session_id}"
        # Ensure any old container is cleaned
        self.stop_desktop(session_id)

        # Inject kubeconfig into Redis for container startup
        self._inject_kubeconfig(session_id, redis_host)

        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "--memory", "1024m",
            "--memory-swap", "1024m",
            "--cpus", "1.5",
            "--pids-limit", "500",
            "--security-opt", "seccomp=unconfined",
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
                if is_admin:
                    redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
                return False

            cid = res.stdout.strip()[:12]
            print(f"[DesktopManager] Started container {container_name} ({cid}) for session {session_id}")

            # Wait up to 15s for desk-agent inside container to register in Redis
            deadline = time.time() + 15.0
            while time.time() < deadline:
                info = redis_bus.get_desktop_info(session_id)
                if info and "host" in info:
                    print(f"[DesktopManager] Desktop registered in Redis: {info}")
                    return True
                time.sleep(0.5)

            if is_admin:
                print(f"[DesktopManager] Timeout waiting for desktop agent registration. Falling back to host VNC for admin.")
                redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
                return True
            else:
                print(f"[DesktopManager] Error: Timeout waiting for container desktop {container_name} registration.")
                return False

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
        try:
            client = redis_bus.get_sync_client()
            if client:
                client.delete(f"session:{session_id}:kubeconfig")
        except Exception:
            pass

    def is_desktop_running(self, session_id: str) -> bool:
        """Checks if desktop container for session_id is currently running."""
        if not session_id or not self.is_docker_available():
            return False
        container_name = f"cka-desktop-{session_id}"
        try:
            res = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return res.returncode == 0 and "true" in res.stdout.lower()
        except Exception:
            return False

    def count_running_desktops(self) -> int:
        """Counts how many cka-desktop-* containers are actively running."""
        if not self.is_docker_available():
            return 0
        try:
            res = subprocess.run(
                ["docker", "ps", "-q", "--filter", "name=cka-desktop-"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if res.returncode == 0 and res.stdout.strip():
                return len([c for c in res.stdout.strip().splitlines() if c.strip()])
        except Exception:
            pass
        return 0


desktop_mgr = DesktopManager()
