from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    reachable = ctx.is_reachable()
    if not reachable and ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 6, "kubeadm node unreachable via SSH", skipped=True)
    workers = []
    if reachable:
        nodes = ctx.get_nodes()
        workers = [n for n in nodes if "node-role.kubernetes.io/control-plane" not in n.get("metadata", {}).get("labels", {})]
        if nodes and not workers:
            workers = nodes
    ready_workers = [
        n for n in workers
        if any(c.get("type") == "Ready" and c.get("status") == "True" for c in n.get("status", {}).get("conditions", []))
    ]
    if workers and len(ready_workers) == len(workers):
        return GradeResult(True, 6, 6, "Worker node re-joined with a fresh bootstrap token and reports Ready")
    if workers and ready_workers:
        return GradeResult(False, 3, 6, f"Only {len(ready_workers)}/{len(workers)} worker nodes Ready (re-bootstrap incomplete)")
    active = ctx.ssh_cmd("NODE_1", "systemctl is-active kubelet")
    if active == "active":
        return GradeResult(False, 3, 6, "Kubelet active on NODE_1 but the worker node is not Ready (token/cert rotation still invalid)")
    if reachable:
        return GradeResult(False, 0, 6, "Cluster reachable but no worker node is Ready (kubelet down or bootstrap token expired)")
    return GradeResult(False, 0, 6, "Worker node not Ready and kubelet not active on NODE_1")
