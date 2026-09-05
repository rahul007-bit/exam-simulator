import os
import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple

# Load .env from repository root if present
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    try:
        with open(_env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

# Re-exported for question graders, which import GradeResult from this module.
from core.models import GradeResult  # noqa: F401


class KubernetesContext:
    def __init__(self, context_name: str = "k3d-cka"):
        self.context_name = context_name
        self.node_1_ip = os.getenv("NODE_1_IP", os.getenv("NODE_1", "127.0.0.1"))
        self.node_2_ip = os.getenv("NODE_2_IP", os.getenv("NODE_2", "127.0.0.1"))
        self.node_3_ip = os.getenv("NODE_3_IP", os.getenv("NODE_3", "127.0.0.1"))
        self.ssh_key_path = os.getenv("SSH_KEY_PATH", os.path.expanduser("~/.ssh/id_rsa"))
        self.ssh_user = os.getenv("SSH_USER", "root")

    def run_cmd(self, cmd: List[str], timeout: int = 4) -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )

    def kubectl(
        self,
        args: List[str],
        namespace: Optional[str] = None,
        as_json: bool = True,
        timeout: int = 4,
    ) -> Any:
        cmd = ["kubectl", "--context", self.context_name]
        if namespace:
            cmd.extend(["-n", namespace])
        cmd.extend(args)
        if as_json:
            cmd.extend(["-o", "json"])

        try:
            res = self.run_cmd(cmd, timeout=timeout)
            if res.returncode != 0:
                return None
            if as_json:
                return json.loads(res.stdout)
            return res.stdout.strip()
        except Exception:
            return None

    def ssh_cmd(
        self,
        node_key: str,
        command: str,
        user: Optional[str] = None,
        timeout: int = 20,
    ) -> Optional[str]:
        user = user or self.ssh_user
        key_path = self.ssh_key_path
        if "1" in node_key or "cp" in node_key or "master" in node_key:
            node_ip = self.node_1_ip
        elif "3" in node_key:
            node_ip = self.node_3_ip
        else:
            node_ip = self.node_2_ip

        cmd = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=5",
            "-i", key_path,
            f"{user}@{node_ip}",
            command,
        ]
        try:
            res = self.run_cmd(cmd, timeout=timeout)
            if res.returncode == 0:
                return res.stdout.strip()
            return None
        except Exception:
            return None

    # --- Assertion Helpers (Flexible Argument Handling) ---

    def _resolve_ns_name(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Tuple[Optional[str], str]:
        """Resolves (namespace, name) flexibly regardless of caller argument order."""
        if namespace is not None:
            return namespace, arg1
        if arg2 is not None:
            # Check if arg1 is namespace and arg2 is name
            return arg1, arg2
        return None, arg1

    def get_pods(self, namespace: str, label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        args = ["get", "pods"]
        if label_selector:
            args.extend(["-l", label_selector])
        data = self.kubectl(args, namespace=namespace)
        if not data or "items" not in data:
            return []
        return data["items"]

    def get_pod(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None, label_selector: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        if name and ns:
            data = self.kubectl(["get", "pod", name], namespace=ns)
            return data if data and data.get("kind") == "Pod" else None
        if ns:
            pods = self.get_pods(ns, label_selector=label_selector)
            return pods[0] if pods else None
        return None

    def get_deployment(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        data = self.kubectl(["get", "deployment", name], namespace=ns)
        return data if data and data.get("kind") == "Deployment" else None

    def get_service(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        data = self.kubectl(["get", "svc", name], namespace=ns)
        return data if data and data.get("kind") == "Service" else None

    def get_endpoints(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        data = self.kubectl(["get", "endpoints", name], namespace=ns)
        return data if data and data.get("kind") == "Endpoints" else None

    def get_pvc(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        data = self.kubectl(["get", "pvc", name], namespace=ns)
        return data if data and data.get("kind") == "PersistentVolumeClaim" else None

    def get_pv(self, name: str) -> Optional[Dict[str, Any]]:
        data = self.kubectl(["get", "pv", name], namespace=None)
        return data if data and data.get("kind") == "PersistentVolume" else None

    def get_ingress(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        data = self.kubectl(["get", "ingress", name], namespace=ns)
        return data if data and data.get("kind") == "Ingress" else None

    def get_configmap(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        data = self.kubectl(["get", "configmap", name], namespace=ns)
        return data if data and data.get("kind") == "ConfigMap" else None

    def get_secret(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        data = self.kubectl(["get", "secret", name], namespace=ns)
        return data if data and data.get("kind") == "Secret" else None

    def get_storageclass(self, name: str) -> Optional[Dict[str, Any]]:
        return self.get_resource("sc", name)

    def get_serviceaccount(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("sa", name, namespace=ns)

    def get_role(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("role", name, namespace=ns)

    def get_rolebinding(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("rolebinding", name, namespace=ns)

    def get_clusterrole(self, name: str) -> Optional[Dict[str, Any]]:
        return self.get_resource("clusterrole", name)

    def get_clusterrolebinding(self, name: str) -> Optional[Dict[str, Any]]:
        return self.get_resource("clusterrolebinding", name)

    def get_networkpolicy(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("netpol", name, namespace=ns)

    def get_statefulset(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("statefulset", name, namespace=ns)

    def get_daemonset(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("daemonset", name, namespace=ns)

    def get_job(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("job", name, namespace=ns)

    def get_cronjob(self, arg1: str, arg2: Optional[str] = None, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
        ns, name = self._resolve_ns_name(arg1, arg2, namespace)
        return self.get_resource("cronjob", name, namespace=ns)

    def check_pod_ready(self, pod: Dict[str, Any]) -> bool:
        if not pod or "status" not in pod:
            return False
        if pod["status"].get("phase") != "Running":
            return False
        container_statuses = pod["status"].get("containerStatuses", [])
        if not container_statuses:
            return False
        return all(cs.get("ready", False) for cs in container_statuses)

    def get_pod_restart_count(self, pod: Dict[str, Any]) -> int:
        if not pod or "status" not in pod:
            return 0
        container_statuses = pod["status"].get("containerStatuses", [])
        return sum(cs.get("restartCount", 0) for cs in container_statuses)

    # --- Generic resource access ---

    RESOURCE_ALIASES = {
        "statefulset": "statefulsets",
        "daemonset": "daemonsets",
        "job": "jobs",
        "cronjob": "cronjobs",
        "hpa": "horizontalpodautoscalers",
        "pdb": "poddisruptionbudgets",
        "serviceaccount": "serviceaccounts",
        "sa": "serviceaccounts",
        "role": "roles.rbac.authorization.k8s.io",
        "rolebinding": "rolebindings.rbac.authorization.k8s.io",
        "clusterrole": "clusterroles.rbac.authorization.k8s.io",
        "clusterrolebinding": "clusterrolebindings.rbac.authorization.k8s.io",
        "netpol": "networkpolicies.networking.k8s.io",
        "quota": "resourcequotas",
        "priorityclass": "priorityclasses.scheduling.k8s.io",
        "storageclass": "storageclasses.storage.k8s.io",
        "sc": "storageclasses.storage.k8s.io",
    }

    def get_resource(
        self, kind: str, name: str, namespace: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        resource = self.RESOURCE_ALIASES.get(kind.lower(), kind.lower())
        args = ["get", resource, name]
        data = self.kubectl(args, namespace=namespace)
        if data and isinstance(data, dict) and "kind" in data and data["kind"] != "Status":
            return data
        return None

    def list_resources(
        self, kind: str, namespace: Optional[str] = None, label_selector: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        resource = self.RESOURCE_ALIASES.get(kind.lower(), kind.lower())
        args = ["get", resource]
        if label_selector:
            args.extend(["-l", label_selector])
        data = self.kubectl(args, namespace=namespace)
        if not data or not isinstance(data, dict) or "items" not in data:
            return []
        return data["items"]

    def get_nodes(self, label_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        args = ["get", "nodes"]
        if label_selector:
            args.extend(["-l", label_selector])
        data = self.kubectl(args)
        if not data or "items" not in data:
            return []
        return data["items"]

    def get_pod_logs(self, namespace: str, name: str, container: Optional[str] = None) -> Optional[str]:
        args = ["logs", name]
        if container:
            args.extend(["-c", container])
        return self.kubectl(args, namespace=namespace, as_json=False)

    def deployment_ready_replicas(self, dep: Optional[Dict[str, Any]]) -> int:
        if not dep:
            return 0
        return int(dep.get("status", {}).get("readyReplicas", 0) or 0)

    def ssh_assert(self, node_key: str, command: str, timeout: int = 20) -> bool:
        """Runs a command over SSH; True only when the command exits 0."""
        return self.ssh_cmd(node_key, command, timeout=timeout) is not None

    def is_reachable(self) -> bool:
        """True when the target cluster answers a trivial request."""
        res = self.run_cmd(["kubectl", "--context", self.context_name, "get", "--raw", "/readyz"], timeout=10)
        return res.returncode == 0
