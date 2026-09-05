from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pods = ctx.get_pods("checkout-prod", label_selector="app=checkout-api")
    pod = pods[0] if pods else None
    if not pod:
        return GradeResult(passed=False, score=0, max_score=3, message="Pod checkout-api not found in checkout-prod")
    if not ctx.check_pod_ready(pod):
        return GradeResult(passed=False, score=0, max_score=3, message=f"Pod is not Ready (Phase: {pod.get('status',{}).get('phase')})")
    if ctx.get_pod_restart_count(pod) > 5:
        return GradeResult(passed=False, score=1, max_score=3, message="Pod is running but has excessive restarts")
    return GradeResult(passed=True, score=3, max_score=3, message="Checkout API is healthy and passing readiness probes")
