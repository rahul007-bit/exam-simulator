from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    pod = ctx.get_pod("frontend-services", "web-frontend")
    if not pod:
        return GradeResult(False, 0, 3, "Pod web-frontend not found in frontend-services")
    inits = pod.get("status", {}).get("initContainerStatuses", []) or []
    pending = [ic.get("name") for ic in inits if not ic.get("ready")]
    if pending:
        return GradeResult(False, 0, 3, "Pod web-frontend stuck in Init:0/1; initContainer(s) " + ", ".join(pending) + " still failing DB host check")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        return GradeResult(False, 1, 3, f"Pod web-frontend passed init but is not Ready (Phase: {phase})")
    restarts = ctx.get_pod_restart_count(pod)
    if restarts > 5:
        return GradeResult(False, 1, 3, f"Pod web-frontend is Ready but crashlooping ({restarts} restarts)")
    return GradeResult(True, 3, 3, "Pod web-frontend is 1/1 Running past its initContainer DNS check")
