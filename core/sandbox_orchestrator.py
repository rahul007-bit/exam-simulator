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

DEFAULT_K3D_CONTEXT = "k3d-cka"


def provision_plan(contexts, kubeadm_context: Optional[str] = None) -> Dict[str, bool]:
    """Decides which sandboxes a session actually needs, from its contexts.

    - `kubeadm`: only when the kubeadm context is among the session contexts.
    - `k3d`: when any non-kubeadm context is present (default when unknown).
    - `desktop`: always (needed for VNC / terminal / browser capture).

    A preset with both contexts returns both `k3d` and `kubeadm` True.
    `contexts=None` preserves the legacy "provision everything" behaviour.
    """
    kubeadm_ctx = kubeadm_context or os.getenv("KUBEADM_CONTEXT", "kubeadm-vms")
    if contexts is None:
        return {"k3d": True, "kubeadm": True, "desktop": True}
    ctxs = {str(c) for c in contexts if c}
    if not ctxs:
        return {"k3d": True, "kubeadm": False, "desktop": True}
    needs_kubeadm = kubeadm_ctx in ctxs
    needs_k3d = any(c != kubeadm_ctx for c in ctxs)
    return {"k3d": needs_k3d, "kubeadm": needs_kubeadm, "desktop": True}


class SandboxOrchestrator:
    def __init__(self):
        # Per-session background fleet thread registry, so teardown can cancel+join
        # provisioning if a session is torn down while its fleet is still in-flight
        # (otherwise the last instances land AFTER the sweep and leak).
        self._fleet_threads: Dict[str, threading.Thread] = {}
        # Per-session cancel flags checked by the fleet thread between steps.
        self._cancel_fleet: Dict[str, bool] = {}

    def _fleet_cancelled(self, session_id: str) -> bool:
        return self._cancel_fleet.get(session_id, False)

    def _attach_fleet_to_desktop(
        self,
        session_id: str,
        ips: Dict[str, str],
        redis_host: str = "172.17.0.1",
        total_timeout: float = 300.0,
    ) -> bool:
        """
        (Re)attaches a provisioned kubeadm fleet to the candidate desktop:
        /etc/hosts aliases, ssh config/key, and a verified kubectl connection.
        Retries until the fleet endpoints are verified operable or timeout —
        a fleet finishing while the desktop container is briefly absent/restarting
        would otherwise leave the session permanently without ssh/kubectl access.
        """
        container = f"cka-desktop-{session_id}"
        deadline = time.time() + total_timeout
        attempt = 0
        verified = False
        while time.time() < deadline and not verified and not self._fleet_cancelled(session_id):
            attempt += 1
            try:
                if not desktop_mgr.is_desktop_running(session_id):
                    print(f"[Orchestrator] Desktop {container} not running (attach "
                          f"attempt {attempt}), waiting to retry...", flush=True)
                    time.sleep(5)
                    continue

                # 1. /etc/hosts aliases (guarded append: no sed -i — /etc/hosts is a
                #    Docker bind mount, so in-place edit via rename fails with EBUSY)
                for role, ip in ips.items():
                    alias = f"{role}-{session_id}"
                    hosts_cmd = (
                        f"grep -qw {alias} /etc/hosts || "
                        f"echo '{ip} {role} {alias}' >> /etc/hosts"
                    )
                    subprocess.run(
                        ["docker", "exec", container, "bash", "-c", hosts_cmd],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
                    )

                # 2. Passwordless root SSH for the candidate (ssh node1, ssh node2)
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
                        ["docker", "exec", container, "bash", "-c", ssh_setup_cmd],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                    )

                    if priv_key_path:
                        subprocess.run(
                            ["docker", "cp", str(priv_key_path), f"{container}:/home/exam/.ssh/id_rsa"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                        )
                        if pub_key_path:
                            subprocess.run(
                                ["docker", "cp", str(pub_key_path), f"{container}:/home/exam/.ssh/id_rsa.pub"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                            )
                        subprocess.run(
                            ["docker", "exec", container, "bash", "-c",
                             "chown -R exam:exam /home/exam/.ssh && chmod 600 /home/exam/.ssh/id_rsa*"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                        )
                except Exception as ex:
                    print(f"[Orchestrator] Warning configuring candidate SSH: {ex}", flush=True)

                # 3. Refresh kubeconfig with the live kubeadm-vms context
                try:
                    desktop_mgr._inject_kubeconfig(session_id, redis_host=redis_host,
                                                  node1_ip=ips.get("node1"))
                except Exception as ex:
                    print(f"[Orchestrator] Warning refreshing kubeconfig: {ex}", flush=True)

                # 4. Verify operability from inside the desktop: host aliases + API reach
                if "node1" in ips:
                    proc = subprocess.run(
                        ["docker", "exec", "-u", "exam", container,
                         "bash", "-c",
                         "getent hosts node1 node2 node3 || true; "
                         "kubectl --context=kubeadm-vms get nodes --no-headers"],
                        capture_output=True, text=True, timeout=60
                    )
                    text = (proc.stdout or "") + (proc.stderr or "")
                    hosts_ok = sum(1 for n in ("node1", "node2", "node3") if f" {n}" in text) >= 3
                    api_ok = "Ready" in text
                    if hosts_ok and api_ok:
                        verified = True
                        print(f"[Orchestrator] Fleet attach VERIFIED for {session_id} "
                              f"(attempt {attempt}): hosts aliases + kubectl OK.", flush=True)
                    else:
                        print(f"[Orchestrator] Fleet attach verify FAILED (attempt {attempt}) "
                              f"for {session_id}: hosts={hosts_ok} api={api_ok} "
                              f"text={(text[:150])!r}; retrying attach loop...", flush=True)
                        time.sleep(8)
                else:
                    # No control plane: aliases-only attach is as good as it gets.
                    verified = True
                    print(f"[Orchestrator] Fleet attach done (no node1) for {session_id}.", flush=True)
            except Exception as e:
                print(f"[Orchestrator] Attach attempt {attempt} error: {e}", flush=True)
                time.sleep(5)
        return verified

    def provision_session(self, session_id: str, redis_host: str = "172.17.0.1", contexts=None) -> Dict[str, Any]:
        """Provisions only the sandboxes the session's questions need.

        `contexts` is the session's `target_contexts`; when omitted the legacy
        behaviour (k3d + desktop + kubeadm fleet) is kept.
        """
        plan = provision_plan(contexts)
        print(
            f"[Orchestrator] Provisioning sandbox for session: {session_id} "
            f"(k3d={plan['k3d']}, kubeadm={plan['kubeadm']}, desktop={plan['desktop']})",
            flush=True,
        )

        # 1. Start Ephemeral k3d Cluster if enabled and needed (ready in ~10-12s)
        enable_k3d = os.getenv("ENABLE_EPHEMERAL_K3D", "1").lower() in ("1", "true")
        k3d_ok = False
        if plan["k3d"] and enable_k3d and k3d_mgr.is_available():
            k3d_ok = k3d_mgr.create_ephemeral_cluster(session_id, redis_host=redis_host)

        # 2. Start Desktop Container with strict caps (ready in ~3s)
        desktop_ok = desktop_mgr.start_desktop(session_id, redis_host=redis_host)

        # 3. If Incus microVMs are enabled AND the session needs kubeadm, provision
        # asynchronously in background (UI launches in ~15s without blocking).
        enable_microvms = os.getenv("ENABLE_MICROVMS", "1").lower() in ("1", "true")
        single_node = os.getenv("SINGLE_NODE", "0").lower() in ("1", "true")

        def _async_fleet_worker():
            try:
                if self._fleet_cancelled(session_id):
                    return
                print(f"[Orchestrator] Background provisioning Incus Kubeadm fleet for session {session_id}...", flush=True)
                ips = incus_mgr.provision_kubeadm_cluster(session_id, is_distributed=(not single_node))
                if self._fleet_cancelled(session_id):
                    # Teardown raced this thread mid-provisioning: the instances just
                    # launched must not leak; clean them up before returning.
                    print(f"[Orchestrator] Fleet provisioning for {session_id} cancelled mid-flight; cleaning up nodes...", flush=True)
                    incus_mgr.delete_session_cluster(session_id)
                    return
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
                if ips:
                    # Verified, retrying attach (hosts aliases + ssh + kubeconfig)
                    self._attach_fleet_to_desktop(session_id, ips, redis_host=redis_host)
                    print(f"[Orchestrator] Incus Kubeadm fleet ready and attached to desktop for {session_id}!", flush=True)
            except Exception as e:
                print(f"[Orchestrator] Exception in background fleet provisioning: {e}", flush=True)
            finally:
                self._fleet_threads.pop(session_id, None)

        if plan["kubeadm"] and enable_microvms and incus_mgr.is_available():
            self._cancel_fleet.pop(session_id, None)
            fleet_thread = threading.Thread(target=_async_fleet_worker, daemon=True, name=f"fleet-bootstrap-{session_id}")
            self._fleet_threads[session_id] = fleet_thread
            fleet_thread.start()

        return {
            "session_id": session_id,
            "k3d_ready": k3d_ok,
            "desktop_ready": desktop_ok,
            "microvms": "provisioning_in_background" if plan["kubeadm"] else "skipped",
        }

    def teardown_session(self, session_id: str) -> bool:
        """Tears down all containers and microVMs for a session, freeing 100% of RAM."""
        print(f"[Orchestrator] Tearing down session sandboxes: {session_id}", flush=True)
        clean_id = session_id.replace("session-", "").replace("-", "")[:10]

        # 0. Deregister FIRST: the moment teardown begins, every auto-restore
        #    path (get_session poll, VNC websocket reconnect) must treat this
        #    session as dead. Resource deletion below takes many seconds; a
        #    browser VNC auto-reconnect during that window otherwise
        #    resurrects the desktop after teardown already stopped it.
        try:
            from core.redis_bus import bus as redis_bus0
            if redis_bus0.is_available():
                redis_bus0.deregister_session(session_id)
                if clean_id:
                    redis_bus0.deregister_session(clean_id)
        except Exception as e:
            print(f"[Orchestrator] Error deregistering session: {e}", flush=True)

        # 0.5 Cancel + join any in-flight fleet provisioning thread FIRST: teardown
        # must not race a thread that is still launching instances, otherwise the
        # remaining nodes land AFTER the sweep below and leak.
        thr = self._fleet_threads.pop(session_id, None)
        if thr is None:
            thr = self._fleet_threads.pop(f"session-{clean_id}", None)
        if thr and thr.is_alive():
            # Do NOT join here (it would block this API call up to ~2 min): just
            # flag cancel; the fleet thread checks it after each step and cleans
            # up its own instances, so nothing leaks past the sweep below.
            print(f"[Orchestrator] Flagging in-flight fleet thread cancelled for {session_id}...", flush=True)
            self._cancel_fleet[session_id] = True

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
                    # NOTE: history:{sid} is NOT deleted here — archive_session
                    # owns it (history must survive teardown for the admin
                    # sessions list).
                    for key in [
                        f"session:{session_id}:kubeconfig",
                        f"session:{session_id}:desktop",
                        f"session:{session_id}:state",
                        f"session:{session_id}",
                        f"token:{session_id}",
                        # Global kubeconfig key survives with a 24h TTL otherwise and
                        # boots the NEXT session's desktop with a dead control-plane IP.
                        "k8s:kubeconfig",
                    ]:
                        client.delete(key)
                    if clean_id:
                        for key in [
                            f"session:{clean_id}:kubeconfig",
                            f"session:{clean_id}:desktop",
                            f"session:{clean_id}:state",
                            f"session:{clean_id}",
                            f"token:{clean_id}",
                            "k8s:kubeconfig",
                        ]:
                            client.delete(key)
        except Exception as e:
            print(f"[Orchestrator] Error cleaning Redis keys: {e}", flush=True)

        return True


orchestrator = SandboxOrchestrator()
