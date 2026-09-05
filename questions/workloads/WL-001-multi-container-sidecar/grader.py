from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("app-logging", "order-processor")
    if not pod:
        return GradeResult(passed=False, score=0, max_score=3, message="Pod order-processor not found in app-logging")
    if not ctx.check_pod_ready(pod):
        return GradeResult(passed=False, score=0, max_score=3, message="Pod order-processor is not Ready (2/2)")
    containers = pod.get("spec", {}).get("containers", [])
    if len(containers) < 2:
        return GradeResult(passed=False, score=1, max_score=3, message=f"Expected 2 containers, found {len(containers)}")
    return GradeResult(passed=True, score=3, max_score=3, message="Multi-container sidecar pod is running 2/2 Ready")
