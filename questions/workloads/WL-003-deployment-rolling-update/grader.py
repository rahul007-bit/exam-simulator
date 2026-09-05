from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    dep = ctx.get_deployment("order-services", "payment-api")
    if not dep:
        return GradeResult(False, 0, 3, "Deployment payment-api not found in order-services")
    strategy = dep.get("spec", {}).get("strategy", {})
    rolling = strategy.get("rollingUpdate", {})
    if str(rolling.get("maxSurge")) != "1" or str(rolling.get("maxUnavailable")) != "0":
        return GradeResult(False, 1, 3, f"RollingUpdate params mismatch: maxSurge={rolling.get('maxSurge')}, maxUnavailable={rolling.get('maxUnavailable')}")
    ready = dep.get("status", {}).get("readyReplicas", 0)
    if ready < 4:
        return GradeResult(False, 2, 3, f"Ready replicas: {ready}/4")
    return GradeResult(True, 3, 3, "payment-api deployment configured with zero-downtime rolling update strategy")
