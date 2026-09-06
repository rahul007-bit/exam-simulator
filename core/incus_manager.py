"""
Incus MicroVM Manager for Kubeadm Multi-Node Clusters
Provisions and destroys ephemeral microVMs for bare-metal CKA tasks (kubeadm, etcd, systemd).
"""
import os
import time
import json
import shutil
import subprocess
from typing import Optional, Dict, Any, List


class IncusClusterManager:
    def __init__(self, remote_host: Optional[str] = None):
        self.remote_host = remote_host
        self._incus_path: Optional[str] = shutil.which("incus")

    def _exec(self, cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
        if self.remote_host and self.remote_host not in ("localhost", "127.0.0.1"):
            remote_cmd = " ".join(cmd)
            full_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", f"root@{self.remote_host}", remote_cmd]
            return subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def is_available(self) -> bool:
        try:
            res = self._exec(["incus", "--version"], timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def launch_node(self, node_name: str, image: str = "images:almalinux/9/cloud", is_vm: bool = True) -> bool:
        """Launches an isolated microVM with strict 2GiB memory and 2 CPU caps."""
        vm_flag = ["--vm"] if is_vm else []
        cmd = [
            "incus", "launch", image, node_name,
            "-c", "limits.cpu=2",
            "-c", "limits.memory=2GiB",
            "-c", "limits.processes=1500"
        ] + vm_flag
        try:
            res = self._exec(cmd, timeout=60)
            return res.returncode == 0
        except Exception as e:
            print(f"[IncusManager] Error launching {node_name}: {e}")
            return False

    def delete_node(self, node_name: str) -> bool:
        """Force deletes an ephemeral microVM node."""
        try:
            res = self._exec(["incus", "delete", "-f", node_name], timeout=30)
            return res.returncode == 0
        except Exception:
            return False

    def get_node_ip(self, node_name: str) -> Optional[str]:
        """Retrieves IPv4 address of an incus instance."""
        try:
            res = self._exec(["incus", "list", node_name, "--format", "json"], timeout=10)
            if res.returncode == 0:
                data = json.loads(res.stdout.strip())
                if data and len(data) > 0:
                    net_info = data[0].get("state", {}).get("network", {})
                    eth0 = net_info.get("eth0", {})
                    for addr in eth0.get("addresses", []):
                        if addr.get("family") == "inet" and addr.get("scope") == "global":
                            return addr.get("address")
        except Exception:
            pass
        return None

    def delete_session_cluster(self, session_id: str):
        for role in ["node1", "node2", "node3"]:
            self.delete_node(f"{role}-{session_id}")


incus_mgr = IncusClusterManager()
