"""
Incus MicroVM Manager for Kubeadm Multi-Node Clusters
Uses native Incus Remotes (TLS on port 8443) to provision and tear down
hardware-accelerated, resource-capped MicroVMs across compute nodes.
"""
import os
import time
import json
import shutil
import subprocess
from typing import Optional, Dict, Any, List


class IncusClusterManager:
    DEFAULT_IMAGE = "k8s-golden"

    def __init__(self):
        self._incus_path: Optional[str] = shutil.which("incus")

    def is_available(self) -> bool:
        if not self._incus_path:
            return False
        try:
            res = subprocess.run(["incus", "--version"], capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def _target_prefix(self, remote_name: Optional[str]) -> str:
        """Returns prefix like 'node1:' or '' if local."""
        if remote_name and remote_name not in ("localhost", "127.0.0.1", "local"):
            return f"{remote_name}:"
        return ""

    def launch_node(
        self,
        node_name: str,
        remote_name: Optional[str] = None,
        image: str = DEFAULT_IMAGE,
        is_vm: bool = False,
        cpu_limit: str = "2",
        mem_limit: str = "2GiB",
    ) -> bool:
        """Launches an isolated container/microVM node with strict CPU, memory, and process limits."""
        if not self.is_available():
            return False

        pfx = self._target_prefix(remote_name)
        target = f"{pfx}{node_name}"
        vm_flag = ["--vm"] if is_vm else []

        cmd = [
            "incus", "launch", f"{pfx}{image}", target,
            "-c", f"limits.cpu={cpu_limit}",
            "-c", f"limits.memory={mem_limit}",
            "-c", "limits.processes=1500",
            "-c", "security.nesting=true",
        ] + vm_flag

        try:
            print(f"[IncusManager] Launching {target} using {image} (CPU={cpu_limit}, MEM={mem_limit})...", flush=True)
            res = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=60
            )
            if res.returncode == 0:
                print(f"[IncusManager] {target} launched successfully.")
                return True
            print(f"[IncusManager] Error launching {target}: {res.stderr.strip()}")
        except Exception as e:
            print(f"[IncusManager] Exception launching {target}: {e}")

        return False

    def delete_node(self, node_name: str, remote_name: Optional[str] = None) -> bool:
        """Force deletes an ephemeral microVM node."""
        if not self.is_available():
            return True

        pfx = self._target_prefix(remote_name)
        target = f"{pfx}{node_name}"
        try:
            res = subprocess.run(["incus", "delete", "-f", target], capture_output=True, text=True, timeout=30)
            return res.returncode == 0
        except Exception:
            return False

    def get_node_ip(self, node_name: str, remote_name: Optional[str] = None) -> Optional[str]:
        """Retrieves IPv4 address of an incus instance."""
        if not self.is_available():
            return None

        pfx = self._target_prefix(remote_name)
        target = f"{pfx}{node_name}"
        try:
            res = subprocess.run(["incus", "list", target, "--format", "json"], capture_output=True, text=True, timeout=10)
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

    def provision_kubeadm_cluster(self, session_id: str, is_distributed: bool = True) -> Dict[str, str]:
        """
        Provisions a complete 3-node Kubeadm cluster for a session.
        In distributed mode: node1 on remote node1, node2 on remote node2, node3 on remote node3.
        In single-node mode: all 3 nodes on local host.
        """
        remotes = {
            "node1": "node1" if is_distributed else None,
            "node2": "node2" if is_distributed else None,
            "node3": "node3" if is_distributed else None,
        }
        limits = {
            "node1": ("2", "2GiB"),
            "node2": ("2", "1.5GiB"),
            "node3": ("2", "1.5GiB"),
        }

        ips = {}
        for role, rem in remotes.items():
            vm_name = f"{role}-{session_id}"
            cpu, mem = limits[role]
            if self.launch_node(vm_name, remote_name=rem, cpu_limit=cpu, mem_limit=mem):
                # Poll up to 15s for IP assignment
                for _ in range(15):
                    ip = self.get_node_ip(vm_name, remote_name=rem)
                    if ip:
                        ips[role] = ip
                        break
                    time.sleep(1)

        return ips

    def delete_session_cluster(self, session_id: str, is_distributed: bool = True):
        remotes = {
            "node1": "node1" if is_distributed else None,
            "node2": "node2" if is_distributed else None,
            "node3": "node3" if is_distributed else None,
        }
        for role, rem in remotes.items():
            self.delete_node(f"{role}-{session_id}", remote_name=rem)

    def list_all_fleet_instances(self) -> List[Dict[str, Any]]:
        """Queries all remotes (local, node1, node2, node3) and returns normalized instance inventory."""
        if not self.is_available():
            return []

        remotes = ["local", "node1", "node2", "node3"]
        fleet_items: List[Dict[str, Any]] = []

        for rem in remotes:
            target = "" if rem == "local" else f"{rem}:"
            try:
                res = subprocess.run(
                    ["incus", "list", target, "--format", "json"],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=8
                )
                if res.returncode == 0 and res.stdout.strip():
                    data = json.loads(res.stdout.strip())
                    for item in data:
                        cfg = item.get("config", {})
                        net_info = item.get("state", {}).get("network", {}) if item.get("state") else {}
                        eth0 = net_info.get("eth0", {})
                        ip = None
                        for addr in eth0.get("addresses", []):
                            if addr.get("family") == "inet" and addr.get("scope") == "global":
                                ip = addr.get("address")
                                break

                        name = item.get("name", "")
                        # Try to extract session_id
                        sid = None
                        if "-" in name:
                            parts = name.split("-", 1)
                            if len(parts) > 1 and ("session" in parts[1] or "mock" in parts[1]):
                                sid = parts[1]

                        fleet_items.append({
                            "name": name,
                            "node": rem,
                            "kind": "incus",
                            "type": item.get("type", "container"),
                            "status": item.get("status", "UNKNOWN"),
                            "ip": ip or "-",
                            "session_id": sid or "-",
                            "cpu_limit": cfg.get("limits.cpu", "-"),
                            "mem_limit": cfg.get("limits.memory", "-"),
                            "created_at": item.get("created_at", "-")
                        })
            except Exception as e:
                print(f"[IncusManager] Error listing instances on {rem}: {e}")

        return fleet_items


incus_mgr = IncusClusterManager()
