"""
Ephemeral Containerized Desktop Manager
Spawns, monitors, and terminates isolated candidate desktops via Docker and Redis.
"""
import os
import time
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
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

    def _inject_kubeconfig(self, session_id: str, redis_host: str = "172.17.0.1", node1_ip: Optional[str] = None) -> None:
        """
        Builds a clean, isolated kubeconfig for the candidate desktop containing ONLY:
    1. 'k3d-cka': the session's active k3d cluster (gateway patched to redis_host).
    2. 'kubeadm-vms': the live Incus multi-node cluster ONLY (never harvested from
       the host kubeconfig, which persists stale contexts across sessions).
    """
        import yaml

        clean_id = session_id.replace("session-", "").replace("-", "")[:10]
        k3d_candidates = [f"cka-{clean_id}", f"cka-{session_id}", f"cka-{session_id[:10]}", "cka"]

        final_clusters = []
        final_contexts = []
        final_users = []
        current_ctx = "k3d-cka"

        # 1. Retrieve the session's active k3d cluster
        k3d_raw = None
        for cname in k3d_candidates:
            try:
                res = subprocess.run(["k3d", "kubeconfig", "get", cname], capture_output=True, text=True, timeout=3)
                if res.returncode == 0 and res.stdout.strip():
                    k3d_raw = res.stdout.strip()
                    break
            except Exception:
                pass

        if k3d_raw:
            try:
                k3d_doc = yaml.safe_load(k3d_raw)
                if isinstance(k3d_doc, dict):
                    orig_clusters = k3d_doc.get("clusters", [])
                    orig_users = k3d_doc.get("users", [])
                    if orig_clusters and orig_users:
                        cl = orig_clusters[0]
                        usr = orig_users[0]
                        srv = cl.get("cluster", {}).get("server", "")
                        if "0.0.0.0" in srv or "127.0.0.1" in srv:
                            srv = srv.replace("0.0.0.0", redis_host).replace("127.0.0.1", redis_host)

                        final_clusters.append({
                            "name": "k3d-cka",
                            "cluster": {
                                "server": srv,
                                "insecure-skip-tls-verify": True,
                            }
                        })
                        final_users.append({
                            "name": "admin@k3d-cka",
                            "user": usr.get("user", {})
                        })
                        final_contexts.append({
                            "name": "k3d-cka",
                            "context": {
                                "cluster": "k3d-cka",
                                "user": "admin@k3d-cka"
                            }
                        })
            except Exception as e:
                print(f"[DesktopManager] Warning parsing k3d kubeconfig: {e}")

        # 2. Check for live Incus node1 kubeadm cluster
        node1_admin_conf = None
        try:
            from core.incus_manager import incus_mgr
            node1_admin_conf = incus_mgr.get_kubeconfig(session_id)
        except Exception:
            pass

        if not node1_admin_conf:
            for remote_prefix in ("node1:", ""):
                try:
                    res = subprocess.run(
                        ["incus", "file", "pull", f"{remote_prefix}node1-{session_id}/etc/kubernetes/admin.conf", "-"],
                        capture_output=True, text=True, timeout=5
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        node1_admin_conf = res.stdout.strip()
                        break
                except Exception:
                    pass

        if node1_admin_conf:
            try:
                node1_doc = yaml.safe_load(node1_admin_conf)
                if isinstance(node1_doc, dict) and node1_doc.get("clusters") and node1_doc.get("users"):
                    n_usr = node1_doc["users"][0]["user"]

                    orig_server = None
                    for c_entry in node1_doc.get("clusters", []):
                        s = c_entry.get("cluster", {}).get("server")
                        if s:
                            orig_server = s
                            break

                    # Resolve node1 IP from Incus or argument
                    resolved_ip = node1_ip
                    if not resolved_ip or resolved_ip == "node1":
                        for r_pfx in ("node1:", ""):
                            try:
                                ip_proc = subprocess.run(
                                    ["incus", "list", f"{r_pfx}node1-{session_id}", "--format", "json"],
                                    capture_output=True, text=True, timeout=3
                                )
                                if ip_proc.returncode == 0:
                                    idata = json.loads(ip_proc.stdout)
                                    if idata and isinstance(idata, list) and len(idata) > 0:
                                        state = idata[0].get("state") or {}
                                        network = state.get("network") or {}
                                        eth0 = network.get("eth0") or {}
                                        for addr in eth0.get("addresses") or []:
                                            if addr.get("family") == "inet" and addr.get("scope") == "global":
                                                resolved_ip = addr.get("address")
                                                break
                                        if resolved_ip and resolved_ip != "node1":
                                            break
                            except Exception:
                                pass

                    if resolved_ip and resolved_ip != "node1":
                        server_endpoint = f"https://{resolved_ip}:6443"
                    elif orig_server:
                        server_endpoint = orig_server
                    else:
                        server_endpoint = "https://node1:6443"

                    final_clusters.append({
                        "name": "kubernetes",
                        "cluster": {
                            "server": server_endpoint,
                            "insecure-skip-tls-verify": True,
                        }
                    })
                    final_users.append({
                        "name": "kubernetes-admin",
                        "user": n_usr
                    })
                    final_contexts.append({
                        "name": "kubeadm-vms",
                        "context": {
                            "cluster": "kubernetes",
                            "user": "kubernetes-admin"
                        }
                    })
            except Exception as e:
                print(f"[DesktopManager] Warning parsing live node1 admin.conf: {e}")

        # kubeadm-vms may ONLY come from the live cluster pull (step 2). There is
        # deliberately NO host-kubeconfig fallback: /root/.kube/config persists
        # across sessions and would make a fresh desktop boot with a stale,
        # unreachable control-plane IP (which does not even exist on a fresh setup).

        if not final_contexts:
            return

        final_doc = {
            "apiVersion": "v1",
            "kind": "Config",
            "current-context": current_ctx,
            "clusters": final_clusters,
            "contexts": final_contexts,
            "users": final_users,
        }
        kube_text = yaml.safe_dump(final_doc, sort_keys=False)

        try:
            client = redis_bus.get_sync_client()
            if client:
                client.setex(f"session:{session_id}:kubeconfig", 86400, kube_text)
                client.setex("k8s:kubeconfig", 86400, kube_text)
                print(f"[DesktopManager] Injected clean isolated kubeconfig ({[c['name'] for c in final_contexts]}) into Redis for session {session_id}")
        except Exception as ex:
            print(f"[DesktopManager] Warning: failed to store kubeconfig in Redis: {ex}")

        # If desktop container is already running, sync kubeconfig into it live
        container_name = f"cka-desktop-{session_id}"
        try:
            r = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", container_name], capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and "true" in r.stdout.lower():
                subprocess.run(["docker", "exec", "-u", "exam", container_name, "mkdir", "-p", "/home/exam/.kube"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                sync_proc = subprocess.Popen(
                    ["docker", "exec", "-i", "-u", "exam", container_name, "tee", "/home/exam/.kube/config"],
                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                sync_proc.communicate(input=kube_text.encode(), timeout=3)
                subprocess.run(["docker", "exec", "-u", "root", container_name, "bash", "-c", "chown -R exam:exam /home/exam/.kube && chmod 600 /home/exam/.kube/config"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                print(f"[DesktopManager] Synced clean kubeconfig into running container {container_name}")
        except Exception:
            pass

        # Also sync to host's ~/.kube/config so deployer and grader have exact matching contexts
        try:
            host_kube_path = Path.home() / ".kube" / "config"
            host_kube_path.parent.mkdir(parents=True, exist_ok=True)
            if host_kube_path.exists() and host_kube_path.is_file():
                try:
                    existing_text = host_kube_path.read_text(encoding="utf-8")
                    host_existing = yaml.safe_load(existing_text) if existing_text.strip() else None
                    if isinstance(host_existing, dict):
                        merged_clusters = {c.get("name"): c for c in host_existing.get("clusters", []) if c.get("name")}
                        merged_contexts = {c.get("name"): c for c in host_existing.get("contexts", []) if c.get("name")}
                        merged_users = {u.get("name"): u for u in host_existing.get("users", []) if u.get("name")}

                        for c in final_clusters:
                            merged_clusters[c["name"]] = c
                        for ctx in final_contexts:
                            merged_contexts[ctx["name"]] = ctx
                        for u in final_users:
                            merged_users[u["name"]] = u

                        merged_doc = {
                            "apiVersion": "v1",
                            "kind": "Config",
                            "current-context": current_ctx or host_existing.get("current-context", ""),
                            "clusters": list(merged_clusters.values()),
                            "contexts": list(merged_contexts.values()),
                            "users": list(merged_users.values()),
                        }
                        host_kube_path.write_text(yaml.safe_dump(merged_doc, sort_keys=False), encoding="utf-8")
                        print(f"[DesktopManager] Merged clean kubeconfig to host {host_kube_path}")
                    else:
                        host_kube_path.write_text(kube_text, encoding="utf-8")
                except Exception:
                    host_kube_path.write_text(kube_text, encoding="utf-8")
            else:
                host_kube_path.write_text(kube_text, encoding="utf-8")
                print(f"[DesktopManager] Synced clean kubeconfig to host {host_kube_path}")
        except Exception as ex:
            print(f"[DesktopManager] Warning syncing host ~/.kube/config: {ex}")

    def cleanup_kubeconfig(self, session_id: str = "all") -> None:
        """
        Removes ephemeral cluster contexts (specifically 'kubeadm-vms') and associated
        clusters/users from the host's ~/.kube/config to prevent stale context pollution.
        Also purges session kubeconfig keys in Redis.
        """
        import yaml
        try:
            host_kube_path = Path.home() / ".kube" / "config"
            if host_kube_path.exists() and host_kube_path.is_file():
                content = host_kube_path.read_text(encoding="utf-8")
                if content.strip():
                    doc = yaml.safe_load(content)
                    if isinstance(doc, dict):
                        contexts = doc.get("contexts") or []
                        clusters = doc.get("clusters") or []
                        users = doc.get("users") or []

                        contexts_to_remove = {"kubeadm-vms"}
                        new_contexts = [c for c in contexts if c.get("name") not in contexts_to_remove]

                        cur_ctx = doc.get("current-context")
                        if cur_ctx in contexts_to_remove:
                            doc["current-context"] = new_contexts[0]["name"] if new_contexts else ""

                        doc["contexts"] = new_contexts
                        referenced_clusters = {c.get("context", {}).get("cluster") for c in new_contexts}
                        referenced_users = {c.get("context", {}).get("user") for c in new_contexts}

                        doc["clusters"] = [c for c in clusters if c.get("name") in referenced_clusters or c.get("name") not in ("kubernetes", "kubeadm-vms")]
                        doc["users"] = [u for u in users if u.get("name") in referenced_users or u.get("name") not in ("kubernetes-admin", "admin@kubeadm-vms")]

                        host_kube_path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
                        print(f"[DesktopManager] Cleaned ephemeral kubeconfig contexts from host {host_kube_path}")
        except Exception as e:
            print(f"[DesktopManager] Warning cleaning host kubeconfig: {e}")

        # Purge Redis keys
        try:
            client = redis_bus.get_sync_client()
            if client:
                client.delete("k8s:kubeconfig")
                if session_id and session_id != "all":
                    clean_id = session_id.replace("session-", "").replace("-", "")[:10]
                    client.delete(f"session:{session_id}:kubeconfig")
                    client.delete(f"session:{clean_id}:kubeconfig")
        except Exception:
            pass

    def verify_container_kubeconfig(self, session_id: str, context: str = "kubeadm-vms") -> bool:
        """
        Verifies operable kubectl communication via docker exec inside cka-desktop-{session_id}.
        """
        if not self.is_docker_available():
            return False
        container_name = f"cka-desktop-{session_id}"
        cmd = ["docker", "exec", "-u", "exam", container_name, "kubectl", f"--context={context}", "get", "nodes"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return res.returncode == 0
        except Exception:
            return False

    def start_desktop(self, session_id: str, redis_host: str = "172.17.0.1") -> bool:
        """Spawns an ephemeral candidate desktop container with full XFCE & kubectl."""
        is_admin = os.getenv("EXAM_ADMIN", "0").lower() in ("1", "true")
        if not self.is_docker_available() or not self.is_image_available():
            if is_admin:
                print(f"[DesktopManager] Container desktop unavailable, falling back to host VNC for admin session {session_id}")
                redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
                return True
            else:
                print(f"[DesktopManager] Container desktop unavailable for candidate session {session_id}")
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

            # Query container IP immediately so Redis has the desktop endpoint without waiting
            container_ip = None
            try:
                ip_res = subprocess.run(
                    ["docker", "inspect", "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}", container_name],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                cip = ip_res.stdout.strip()
                if cip:
                    container_ip = cip
                    redis_bus.set_desktop_info(session_id, host=cip, vnc_port=5901, ws_port=6080)
                    print(f"[DesktopManager] Injected container IP {cip} directly into Redis for session {session_id}")
            except Exception as e:
                print(f"[DesktopManager] Failed to inspect container IP: {e}")

            # Wait up to 15s for desk-agent inside container to register in Redis
            deadline = time.time() + 15.0
            while time.time() < deadline:
                info = redis_bus.get_desktop_info(session_id)
                if info and info.get("host") and info.get("host") not in ("127.0.0.1", "localhost"):
                    print(f"[DesktopManager] Desktop registered in Redis: {info}")
                    return True
                time.sleep(0.5)

            if container_ip:
                return True

            if is_admin:
                print(f"[DesktopManager] Timeout waiting for desktop agent registration. Falling back to host VNC for admin.")
                redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
                return True
            else:
                print(f"[DesktopManager] Error: Timeout waiting for container desktop {container_name} registration.")
                return False

        except Exception as e:
            print(f"[DesktopManager] Exception starting container: {e}")
            if is_admin:
                redis_bus.set_desktop_info(session_id, host="127.0.0.1", vnc_port=5901, ws_port=6080)
            return False

    def stop_desktop(self, session_id: str) -> None:
        """Terminates and removes desktop container and cleans Redis state."""
        clean_id = session_id.replace("session-", "").replace("-", "")[:10]
        candidate_names = [
            f"cka-desktop-{session_id}",
            f"cka-desktop-session-{clean_id}",
            f"cka-desktop-{clean_id}",
        ]

        if self.is_docker_available():
            for cname in candidate_names:
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", cname],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                    )
                except Exception:
                    pass

            # Sweep any container with session_id or clean_id in name
            try:
                ps_res = subprocess.run(
                    ["docker", "ps", "-a", "--format", "{{.Names}}"],
                    capture_output=True, text=True, timeout=5
                )
                if ps_res.returncode == 0 and ps_res.stdout.strip():
                    for name in ps_res.stdout.strip().splitlines():
                        name = name.strip()
                        if name.startswith("cka-desktop-") and (clean_id in name or session_id in name):
                            subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            except Exception:
                pass

        redis_bus.clear_desktop_info(session_id)
        if clean_id != session_id:
            redis_bus.clear_desktop_info(clean_id)
            redis_bus.clear_desktop_info(f"session-{clean_id}")

        try:
            client = redis_bus.get_sync_client()
            if client:
                client.delete(f"session:{session_id}:kubeconfig")
                client.delete(f"session:{clean_id}:kubeconfig")
                client.delete(f"session:session-{clean_id}:kubeconfig")
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

    def is_container_running(self, session_id: str) -> bool:
        """Alias for is_desktop_running."""
        return self.is_desktop_running(session_id)


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

    def list_all_docker_containers(self) -> List[Dict[str, Any]]:
        """Lists all docker containers with session mapping and status."""
        if not self.is_docker_available():
            return []
        try:
            res = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{json .}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            containers = []
            if res.returncode == 0 and res.stdout.strip():
                import json
                for line in res.stdout.strip().splitlines():
                    if not line.strip():
                        continue
                    try:
                        c = json.loads(line)
                        names = c.get("Names", "")
                        sid = None
                        if "cka-desktop-" in names:
                            sid = names.replace("cka-desktop-", "")
                        elif "k3d-cka-" in names:
                            sid = names.replace("k3d-cka-", "").split("-")[0]

                        containers.append({
                            "name": names,
                            "node": "mgmt (10.8.0.15)",
                            "kind": "docker",
                            "type": "container",
                            "image": c.get("Image", "-"),
                            "status": c.get("State", c.get("Status", "-")),
                            "session_id": sid or "-",
                            "created_at": c.get("CreatedAt", "-")
                        })
                    except Exception:
                        pass
            return containers
        except Exception:
            return []


desktop_mgr = DesktopManager()
