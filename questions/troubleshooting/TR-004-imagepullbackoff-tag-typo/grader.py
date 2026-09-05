from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    dep = ctx.get_deployment("warehouse", "inventory-svc")
    if not dep:
        return GradeResult(False, 0, 2, "Deployment inventory-svc not found")
    ready = dep.get("status", {}).get("readyReplicas", 0)
    if ready < 2:
        return GradeResult(False, 0, 2, f"Ready replicas: {ready}/2")
    return GradeResult(True, 2, 2, "Inventory service is healthy with 2/2 ready pods")
