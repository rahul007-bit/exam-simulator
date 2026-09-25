"""
Ephemeral k3d Cluster Manager
Provisions, resource-caps, and destroys isolated k3s clusters per candidate exam session.
"""
import os
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from core.redis_bus import bus as redis_bus


class K3dClusterManager:
    K3S_IMAGE = "rancher/k3s:v1.30.2-k3s1"

    def __init__(self):
        self._k3d_path: Optional[str] = shutil.which("k3d")

    def is_available(self) -> bool:
        return self._k3d_path is not None

    def _cluster_name(self, session_id: str) -> str:
        clean_id = session_id.replace("session-", "").replace("-", "")[:10]
        return f"cka-{clean_id}"

    def create_ephemeral_cluster(self, session_id: str, redis_host: str = "172.17.0.1") -> bool:
        """
        Creates an isolated, resource-constrained k3d cluster for this session.
        Applies strict 1024m server / 768m agent cgroup limits and system-reserved headroom.
        """
        if not self.is_available():
            print(f"[K3dManager] k3d CLI not found on host, skipping cluster creation")
            return False

        kname = self._cluster_name(session_id)
        # Clean up any stale cluster with this name
        self.delete_ephemeral_cluster(session_id)

        print(f"[K3dManager] Provisioning ephemeral cluster '{kname}' for session '{session_id}' with strict resource caps...", flush=True)

        cmd = [
            "k3d", "cluster", "create", kname,
            "--image", self.K3S_IMAGE,
            "--agents", "1",
            "--servers-memory", "1024m",
            "--agents-memory", "768m",
            "--k3s-arg", "--disable=traefik@server:0",
            "--k3s-arg", "--kubelet-arg=system-reserved=cpu=100m,memory=150Mi@all",
            "--no-lb",
            "--wait"
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            if res.returncode != 0:
                print(f"[K3dManager] k3d create failed: {res.stderr.strip()}")
                return False

            print(f"[K3dManager] Cluster '{kname}' created successfully. Configuring kubeconfig...", flush=True)

            # Export kubeconfig
            kube_res = subprocess.run(["k3d", "kubeconfig", "get", kname], capture_output=True, text=True, timeout=10)
            if kube_res.returncode == 0 and kube_res.stdout.strip():
                kube_text = kube_res.stdout.strip()

                # Rewrite context to standardized k3d-cka
                import yaml
                try:
                    doc = yaml.safe_load(kube_text)
                    if isinstance(doc, dict):
                        for c in doc.get("contexts", []):
                            c["name"] = "k3d-cka"
                        doc["current-context"] = "k3d-cka"

                        # Ensure server endpoint is accessible from container
                        for cl in doc.get("clusters", []):
                            srv = cl.get("cluster", {}).get("server", "")
                            if "0.0.0.0" in srv or "127.0.0.1" in srv:
                                cl["cluster"]["server"] = srv.replace("0.0.0.0", redis_host).replace("127.0.0.1", redis_host)
                                cl["cluster"].pop("certificate-authority-data", None)
                                cl["cluster"]["insecure-skip-tls-verify"] = True

                        kube_text = yaml.safe_dump(doc, sort_keys=False)
                except Exception as e:
                    print(f"[K3dManager] Warning rewriting kubeconfig: {e}")

                # Store in Redis for container entrypoint & deployer
                client = redis_bus.get_sync_client()
                if client:
                    client.setex(f"session:{session_id}:kubeconfig", 86400, kube_text)
                    client.setex("k8s:kubeconfig", 86400, kube_text)

                # Save locally for host grader/deployer
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml") as f:
                    f.write(kube_text)
                    tmp_kube = f.name

                # Compatibility label: ensure ST-005 and node selectors match
                try:
                    subprocess.run(
                        ["kubectl", "--kubeconfig", tmp_kube, "label", "node", f"k3d-{kname}-server-0",
                         "kubernetes.io/hostname=k3d-cka-server-0", "--overwrite"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5
                    )
                except Exception:
                    pass

                try:
                    os.unlink(tmp_kube)
                except Exception:
                    pass

                print(f"[K3dManager] Ephemeral cluster '{kname}' ready with context 'k3d-cka'.")
                return True

        except Exception as ex:
            print(f"[K3dManager] Exception creating cluster: {ex}")
            return False

        return False

    def delete_ephemeral_cluster(self, session_id: str) -> bool:
        """Destroys the ephemeral cluster and frees 100% of RAM/CPU."""
        if not self.is_available():
            return True

        clean_id = session_id.replace("session-", "").replace("-", "")[:10]
        kname = self._cluster_name(session_id)
        target_clusters = {kname, f"cka-{session_id}", f"cka-{clean_id}"}

        # Scan live k3d clusters
        try:
            res = subprocess.run(["k3d", "cluster", "list", "--no-headers"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    parts = line.split()
                    if parts:
                        cl_name = parts[0]
                        if cl_name.startswith("cka-") and (clean_id in cl_name or session_id in cl_name):
                            target_clusters.add(cl_name)
        except Exception as e:
            print(f"[K3dManager] Warning listing clusters: {e}")

        success = True
        for target in target_clusters:
            try:
                r = subprocess.run(["k3d", "cluster", "delete", target], capture_output=True, text=True, timeout=30)
                if r.returncode == 0:
                    print(f"[K3dManager] Deleted ephemeral cluster '{target}'.")
            except Exception as e:
                print(f"[K3dManager] Warning deleting cluster '{target}': {e}")
                success = False

        # Extra safety: remove any dangling docker containers for this cluster
        try:
            ps_res = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=5
            )
            if ps_res.returncode == 0 and ps_res.stdout.strip():
                for name in ps_res.stdout.strip().splitlines():
                    name = name.strip()
                    if name.startswith("k3d-cka-") and (clean_id in name or session_id in name):
                        subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        except Exception:
            pass

        return success


k3d_mgr = K3dClusterManager()
