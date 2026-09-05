from core.graderlib import KubernetesContext, GradeResult

MANIFEST = "/etc/kubernetes/manifests/node-monitor.yaml"

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 4, "kubeadm node NODE_1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", "true") is None:
        return GradeResult(False, 0, 4, "kubeadm node unreachable via SSH", skipped=True)
    content = ctx.ssh_cmd("NODE_1", f"cat {MANIFEST} 2>/dev/null")
    if not content:
        return GradeResult(False, 0, 4, f"Static pod manifest {MANIFEST} not found on control-plane node")
    low = content.lower()
    if "kind: pod" not in low or "apiversion" not in low:
        return GradeResult(False, 1, 4, f"{MANIFEST} exists but is not a valid Pod manifest (missing apiVersion/kind)")
    if "busybox:1.36" not in content:
        return GradeResult(False, 1, 4, f"Manifest is a Pod but image busybox:1.36 not found in {MANIFEST}")
    if "sleep" not in low or "3600" not in low:
        return GradeResult(False, 2, 4, f"Manifest uses busybox:1.36 but the container command does not run sleep 3600")
    pod = ctx.ssh_cmd(
        "NODE_1",
        "kubectl get pods --kubeconfig=/etc/kubernetes/admin.conf 2>/dev/null | grep node-monitor | grep -c Running",
    )
    if not pod or pod.strip() == "0":
        return GradeResult(False, 3, 4, "Manifest correct but no node-monitor pod in Running state in the cluster (kubelet has not started it)")
    return GradeResult(True, 4, 4, f"Static pod node-monitor manifest valid and running ({pod.strip()} Running pod)")
