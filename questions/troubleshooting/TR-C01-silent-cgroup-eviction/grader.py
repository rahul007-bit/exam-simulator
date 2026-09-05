from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    dep = ctx.get_deployment("cgroup-limits", "critical-api")
    if not dep:
        return GradeResult(False, 0, 6, "Deployment critical-api not found")
    ready = dep.get("status", {}).get("readyReplicas", 0)
    if ready < 3:
        return GradeResult(False, 0, 6, f"Ready replicas: {ready}/3 (Check ResourceQuota restrictions)")
    return GradeResult(True, 6, 6, "ResourceQuota satisfied and critical-api running 3/3 ready")
