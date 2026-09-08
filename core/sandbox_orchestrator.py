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
import subprocess
import threading
from pathlib import Path
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

        # 1. Start Ephemeral k3d Cluster if enabled (ready in ~10-12s)
        enable_k3d = os.getenv("ENABLE_EPHEMERAL_K3D", "1").lower() in ("1", "true")
        k3d_ok = False
        if enable_k3d and k3d_mgr.is_available():
            k3d_ok = k3d_mgr.create_ephemeral_cluster(session_id, redis_host=redis_host)

        # 2. Start Desktop Container with strict caps (ready in ~3s)
        desktop_ok = desktop_mgr.start_desktop(session_id, redis_host=redis_host)

        # 3. If Incus microVMs are enabled, provision asynchronously in background thread
        # This guarantees candidate UI launches in ~15 seconds without blocking for 2 minutes!
        enable_microvms = os.getenv("ENABLE_MICROVMS", "1").lower() in ("1", "true")
        single_node = os.getenv("SINGLE_NODE", "0").lower() in ("1", "true")

        def _async_fleet_worker():
            try:
                print(f"[Orchestrator] Background provisioning Incus Kubeadm fleet for session {session_id}...", flush=True)
                ips = incus_mgr.provision_kubeadm_cluster(session_id, is_distributed=(not single_node))
                if ips:
                    # Expose live container IPs to question setup.sh scripts and graders,
                    # which drive nodes over SSH via NODE_1/NODE_2/NODE_3.
                    try:
                        for role, ip in ips.items():
                            os.environ[f"NODE_{role[-1]}"] = ip
                        if redis_bus.is_available():
                            client = redis_bus.get_sync_client()
                            if client:
                                import json as _json
                                client.setex(f"session:{session_id}:nodeenv", 86400, _json.dumps(ips))
                    except Exception as ex:
                        print(f"[Orchestrator] Warning publishing node env: {ex}")
                if ips and desktop_mgr.is_desktop_running(session_id):
                    # 1. Update /etc/hosts for role resolution
                    for role, ip in ips.items():
                        try:
                            subprocess.run(
                                ["docker", "exec", f"cka-desktop-{session_id}", "bash", "-c", f"echo '{ip} {role} {role}-{session_id}' >> /etc/hosts"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                            )
                        except Exception:
                            pass

                    # 2. Configure passwordless root SSH for candidate user exam (ssh node1, ssh node2)
                    try:
                        priv_key_path = None
                        pub_key_path = None
                        for key_cand in (Path("/root/.ssh/id_ed25519"), Path("/root/.ssh/id_rsa")):
                            if key_cand.exists() and key_cand.is_file():
                                priv_key_path = key_cand
                                pub_cand = key_cand.with_suffix(".pub")
                                if pub_cand.exists():
                                    pub_key_path = pub_cand
                                break

                        ssh_setup_cmd = (
                            "mkdir -p /home/exam/.ssh && "
                            "printf 'Host node1 node2 node3 node1-* node2-* node3-*\\n  User root\\n  StrictHostKeyChecking no\\n  UserKnownHostsFile /dev/null\\n  LogLevel ERROR\\n\\nHost *\\n  StrictHostKeyChecking no\\n  UserKnownHostsFile /dev/null\\n  LogLevel ERROR\\n' > /home/exam/.ssh/config && "
                            "chmod 700 /home/exam/.ssh && chmod 600 /home/exam/.ssh/config && chown -R exam:exam /home/exam/.ssh"
                        )
                        subprocess.run(
                            ["docker", "exec", f"cka-desktop-{session_id}", "bash", "-c", ssh_setup_cmd],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                        )

                        if priv_key_path:
                            subprocess.run(
                                ["docker", "cp", str(priv_key_path), f"cka-desktop-{session_id}:/home/exam/.ssh/id_rsa"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                            )
                            if pub_key_path:
                                subprocess.run(
                                    ["docker", "cp", str(pub_key_path), f"cka-desktop-{session_id}:/home/exam/.ssh/id_rsa.pub"],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                                )
                            subprocess.run(
                                ["docker", "exec", f"cka-desktop-{session_id}", "bash", "-c", "chown -R exam:exam /home/exam/.ssh && chmod 600 /home/exam/.ssh/id_rsa*"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                            )
                    except Exception as ex:
                        print(f"[Orchestrator] Warning configuring candidate SSH: {ex}")

                    # 3. Refresh and inject clean kubeconfig with live kubeadm-vms context
                    try:
                        desktop_mgr._inject_kubeconfig(session_id, redis_host=redis_host, node1_ip=ips.get("node1"))
                        print(f"[Orchestrator] Kubeconfig updated with kubeadm-vms context for session {session_id}")
                    except Exception as ex:
                        print(f"[Orchestrator] Warning refreshing kubeconfig: {ex}")

                    print(f"[Orchestrator] Incus Kubeadm fleet ready and attached to desktop for {session_id}!", flush=True)
            except Exception as e:
                print(f"[Orchestrator] Exception in background fleet provisioning: {e}", flush=True)

        if enable_microvms and incus_mgr.is_available():
            fleet_thread = threading.Thread(target=_async_fleet_worker, daemon=True, name=f"fleet-bootstrap-{session_id}")
            fleet_thread.start()

        return {
            "session_id": session_id,
            "k3d_ready": k3d_ok,
            "desktop_ready": desktop_ok,
            "microvms": "provisioning_in_background"
        }

    def teardown_session(self, session_id: str) -> bool:
        """Tears down all containers and microVMs for a session, freeing 100% of RAM."""
        print(f"[Orchestrator] Tearing down session sandboxes: {session_id}", flush=True)
        clean_id = session_id.replace("session-", "").replace("-", "")[:10]

        # 1. Candidate desktop container
        try:
            desktop_mgr.stop_desktop(session_id)
        except Exception as e:
            print(f"[Orchestrator] Error stopping desktop: {e}", flush=True)

        # 2. k3d ephemeral cluster
        try:
            k3d_mgr.delete_ephemeral_cluster(session_id)
        except Exception as e:
            print(f"[Orchestrator] Error deleting k3d cluster: {e}", flush=True)

        # 3. Incus microVMs across all remotes
        try:
            incus_mgr.delete_session_cluster(session_id)
        except Exception as e:
            print(f"[Orchestrator] Error deleting Incus cluster: {e}", flush=True)

        # 4. Cleanup Redis session info & tokens
        try:
            from core.redis_bus import bus as redis_bus
            if redis_bus.is_available():
                # Deregister BEFORE key cleanup so auto-restore paths immediately
                # treat this session as dead (prevents desktop resurrection).
                try:
                    redis_bus.deregister_session(session_id)
                    if clean_id:
                        redis_bus.deregister_session(clean_id)
                except Exception:
                    pass
                client = redis_bus.get_sync_client()
                if client:
                    for key in [
                        f"session:{session_id}:kubeconfig",
                        f"session:{session_id}:desktop",
                        f"session:{session_id}:state",
                        f"session:{session_id}",
                        f"token:{session_id}",
                        f"history:{session_id}",
                    ]:
                        client.delete(key)
                    if clean_id:
                        for key in [
                            f"session:{clean_id}:kubeconfig",
                            f"session:{clean_id}:desktop",
                            f"session:{clean_id}:state",
                            f"session:{clean_id}",
                            f"token:{clean_id}",
                            f"history:{clean_id}",
                        ]:
                            client.delete(key)
        except Exception as e:
            print(f"[Orchestrator] Error cleaning Redis keys: {e}", flush=True)

        return True


orchestrator = SandboxOrchestrator()
