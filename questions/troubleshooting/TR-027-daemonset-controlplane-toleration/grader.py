from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    ds = ctx.get_resource("daemonset", "node-exporter", "monitoring-ns")
    if not ds:
        return GradeResult(False, 0, 4, "DaemonSet node-exporter not found in monitoring-ns")
    nodes = ctx.get_nodes()
    if not nodes:
        return GradeResult(False, 0, 4, "No nodes found in cluster")
    ready = ds.get("status", {}).get("numberReady", 0) or 0
    tolerations = ds.get("spec", {}).get("template", {}).get("spec", {}).get("tolerations", []) or []
    has_tol = any(
        t.get("operator") == "Exists" or t.get("key") in ("node-role.kubernetes.io/control-plane", "node-role.kubernetes.io/master")
        for t in tolerations
    )
    if ready < 1:
        return GradeResult(False, 0, 4, "No ready node-exporter pods in monitoring-ns")
    if not has_tol:
        return GradeResult(False, 2, 4, f"node-exporter runs on {ready}/{len(nodes)} nodes but toleration for node-role.kubernetes.io/control-plane:NoSchedule is missing")
    if ready < len(nodes):
        return GradeResult(False, 2, 4, f"Toleration present but node-exporter runs on only {ready}/{len(nodes)} nodes")
    return GradeResult(True, 4, 4, f"node-exporter runs on all {len(nodes)} nodes including control-plane")
