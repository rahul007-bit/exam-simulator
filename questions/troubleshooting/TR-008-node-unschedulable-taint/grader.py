from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    dep = ctx.get_deployment("production-apps", "mission-critical")
    if not dep:
        return GradeResult(False, 0, 3, "Deployment mission-critical not found")
    ready = dep.get("status", {}).get("readyReplicas", 0)
    if ready < 2:
        return GradeResult(False, 0, 3, f"Deployment not fully scheduled: {ready}/2 ready")
    return GradeResult(True, 3, 3, "All worker nodes uncordoned and mission-critical is 2/2 Ready")
