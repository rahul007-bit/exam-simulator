from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_2", "echo up") != "up":
        return GradeResult(False, 0, 4, "kubeadm node node2 unreachable via SSH", skipped=True)
    conf = ctx.ssh_cmd("NODE_2", "grep -i cgroupDriver /var/lib/kubelet/config.yaml")
    if not conf or "systemd" not in conf.lower():
        current = conf.strip() if conf else "no cgroupDriver entry"
        return GradeResult(False, 0, 4, f"/var/lib/kubelet/config.yaml on node2 cgroupDriver is not systemd ({current})")
    active = ctx.ssh_cmd("NODE_2", "systemctl is-active kubelet")
    if active != "active":
        return GradeResult(False, 2, 4, "cgroupDriver is systemd but kubelet service is not active on node2")
    if ctx.is_reachable():
        node = next((n for n in ctx.get_nodes() if n.get("metadata", {}).get("name") == "node2"), None)
        if node:
            conds = node.get("status", {}).get("conditions", [])
            ready = any(c.get("type") == "Ready" and c.get("status") == "True" for c in conds)
            if not ready:
                return GradeResult(False, 3, 4, "Kubelet is active on node2 but node2 is not Ready yet in cluster")
    return GradeResult(True, 4, 4, "Kubelet cgroupDriver on node2 is systemd, service active, and node Ready")
