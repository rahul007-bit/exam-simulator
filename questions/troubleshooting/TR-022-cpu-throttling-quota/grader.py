from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    dep = ctx.get_deployment("analytics", "data-sync")
    if not dep:
        return GradeResult(False, 0, 3, "Deployment data-sync not found in analytics")
    ready = ctx.deployment_ready_replicas(dep)
    if ready < 2:
        return GradeResult(False, 1 if ready >= 1 else 0, 3, f"data-sync has {ready}/2 ready replicas; namespace CPU ResourceQuota still blocks pod creation")
    return GradeResult(True, 3, 3, "ResourceQuota no longer throttles data-sync: 2/2 ready replicas")
