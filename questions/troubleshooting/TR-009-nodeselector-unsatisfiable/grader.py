from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("analytics", "analytics-worker")
    if not pod:
        return GradeResult(False, 0, 3, "Pod analytics-worker not found")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 0, 3, f"Pod is not Ready (Phase: {pod.get('status',{}).get('phase')})")
    return GradeResult(True, 3, 3, "analytics-worker scheduled and running")
