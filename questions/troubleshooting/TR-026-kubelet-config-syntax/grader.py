from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    nodes = ctx.get_nodes()
    if not nodes:
        return GradeResult(False, 0, 3, "No nodes returned by the cluster")
    notready = []
    for n in nodes:
        conds = n.get("status", {}).get("conditions", []) or []
        if not any(c.get("type") == "Ready" and c.get("status") == "True" for c in conds):
            notready.append(n["metadata"]["name"])
    if notready:
        return GradeResult(False, 0, 3, "Node(s) " + ", ".join(notready) + " not Ready; kubelet config still broken")
    return GradeResult(True, 3, 3, f"All {len(nodes)} node(s) Ready; kubelet service is active with valid config")
