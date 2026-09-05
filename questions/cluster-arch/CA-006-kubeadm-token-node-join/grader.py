from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 3, "kubeadm node node1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_3", "echo up") != "up":
        return GradeResult(False, 0, 3, "kubeadm node node3 unreachable via SSH", skipped=True)

    names = ctx.ssh_cmd(
        "NODE_1",
        "kubectl get nodes --kubeconfig=/etc/kubernetes/admin.conf -o jsonpath='{.items[*].metadata.name}' 2>/dev/null",
    )
    if not names or "node3" not in names.split():
        return GradeResult(False, 0, 3, f"Node node3 not registered in cluster; current nodes: {names or 'query failed'}")

    ready = ctx.ssh_cmd(
        "NODE_1",
        "kubectl get node node3 --kubeconfig=/etc/kubernetes/admin.conf -o jsonpath='{.status.conditions[?(@.type==\"Ready\")].status}' 2>/dev/null",
    )
    if not ready or ready.strip() != "True":
        return GradeResult(False, 2, 3, "Node node3 joined the cluster but is not Ready yet")

    return GradeResult(True, 3, 3, "Node node3 joined the cluster and is Ready")
