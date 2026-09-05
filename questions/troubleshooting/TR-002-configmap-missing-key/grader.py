from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("auth-system", "auth-api")
    if not pod:
        return GradeResult(passed=False, score=0, max_score=2, message="Pod auth-api not found in auth-system")
    if not ctx.check_pod_ready(pod):
        if not ctx.wait_pod_ready("auth-system", "auth-api", timeout=10):
            return GradeResult(passed=False, score=0, max_score=2, message="Pod auth-api is not Ready")
    return GradeResult(passed=True, score=2, max_score=2, message="auth-api started successfully with valid ConfigMap key")
