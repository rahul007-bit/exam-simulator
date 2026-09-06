"""
Unified Sandbox Orchestrator
Coordinates the full lifecycle of candidate exam environments:
- Desktop Container (noVNC + xterm + browser)
- Ephemeral k3d Cluster (standard workloads)
- Ephemeral Kubeadm MicroVMs (node / systemd / etcd drills)
All components are strictly resource-capped.
"""
import os
import time
from typing import Dict, Any, Optional
from core.desktop_manager import desktop_mgr
from core.k3d_manager import k3d_mgr
from core.incus_manager import incus_mgr
from core.redis_bus import bus as redis_bus


class SandboxOrchestrator:
    def __init__(self):
        pass

    def provision_session(self, session_id: str, redis_host: str = "172.17.0.1") -> Dict[str, Any]:
        """Provisions all sandboxes for an exam session with strict resource limits."""
        print(f"[Orchestrator] Provisioning isolated sandbox for session: {session_id}", flush=True)

        # 1. Start Ephemeral k3d Cluster if enabled
        enable_k3d = os.getenv("ENABLE_EPHEMERAL_K3D", "1").lower() in ("1", "true")
        k3d_ok = False
        if enable_k3d and k3d_mgr.is_available():
            k3d_ok = k3d_mgr.create_ephemeral_cluster(session_id, redis_host=redis_host)

        # 2. Start Desktop Container with strict caps (1GB RAM, 1.5 CPUs, 500 PIDs)
        desktop_ok = desktop_mgr.start_desktop(session_id, redis_host=redis_host)

        # 3. If Incus microVMs are enabled, spawn them
        enable_microvms = os.getenv("ENABLE_MICROVMS", "0").lower() in ("1", "true")
        microvm_ips = {}
        if enable_microvms and incus_mgr.is_available():
            for role in ["node1", "node2", "node3"]:
                vm_name = f"{role}-{session_id}"
                if incus_mgr.launch_node(vm_name):
                    ip = incus_mgr.get_node_ip(vm_name)
                    if ip:
                        microvm_ips[role] = ip

        return {
            "session_id": session_id,
            "k3d_ready": k3d_ok,
            "desktop_ready": desktop_ok,
            "microvms": microvm_ips
        }

    def teardown_session(self, session_id: str) -> bool:
        """Tears down all containers and microVMs for a session, freeing 100% of RAM."""
        print(f"[Orchestrator] Tearing down session sandboxes: {session_id}", flush=True)
        desktop_mgr.stop_desktop(session_id)
        k3d_mgr.delete_ephemeral_cluster(session_id)
        incus_mgr.delete_session_cluster(session_id)
        return True


orchestrator = SandboxOrchestrator()
