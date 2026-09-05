from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 3, "kubeadm node node1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_2", "echo up") != "up":
        return GradeResult(False, 0, 3, "kubeadm node node2 unreachable via SSH", skipped=True)

    # Determine target version from control plane node1 (e.g. "v1.36.4")
    cp_ver = ctx.ssh_cmd(
        "NODE_1",
        "kubectl get node node1 --kubeconfig=/etc/kubernetes/admin.conf -o jsonpath='{.status.nodeInfo.kubeletVersion}' 2>/dev/null",
    )
    target_version = cp_ver.strip() if cp_ver else "v1.36.4"

    worker = ctx.ssh_cmd("NODE_2", "hostname").strip() or "node2"
    kubelet_ver = ctx.ssh_cmd("NODE_2", "kubelet --version 2>/dev/null")
    kubelet_ok = bool(kubelet_ver) and target_version in kubelet_ver
    if not kubelet_ok:
        return GradeResult(False, 0, 3, f"Worker kubelet binary on node2 is not {target_version} (got {kubelet_ver or 'unavailable'})")

    node_info = ctx.ssh_cmd(
        "NODE_1",
        f"kubectl get node {worker} --kubeconfig=/etc/kubernetes/admin.conf -o jsonpath='{{.status.nodeInfo.kubeletVersion}}|{{.spec.unschedulable}}' 2>/dev/null",
    )
    if not node_info or "|" not in node_info:
        return GradeResult(False, 1, 3, f"Worker kubelet at {target_version} but node {worker} not queryable via control-plane kubectl")

    ver, unsched = node_info.strip().split("|", 1)
    if ver != target_version:
        return GradeResult(False, 1, 3, f"Node {worker} is at kubeletVersion {ver}, expected {target_version}")

    if unsched.strip() == "true":
        return GradeResult(False, 2, 3, f"Node {worker} upgraded to {ver} but still cordoned (spec.unschedulable=true; uncordon node2 after upgrade)")

    ready = ctx.ssh_cmd("NODE_1", f"kubectl get node {worker} --kubeconfig=/etc/kubernetes/admin.conf 2>/dev/null | grep -c ' Ready '")
    if not ready or ready.strip() == "0":
        return GradeResult(False, 2, 3, f"Node {worker} is {target_version} and uncordoned but not Ready")

    return GradeResult(True, 3, 3, f"Worker {worker} upgraded to {ver}, uncordoned, and Ready")
