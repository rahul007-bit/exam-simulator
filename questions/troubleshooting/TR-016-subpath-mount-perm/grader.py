from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    pod = ctx.get_pod("api-backend", "api-app")
    if not pod:
        return GradeResult(False, 0, 4, "Pod api-app not found in api-backend")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        waiting = pod.get("status", {}).get("containerStatuses", [{}])[0].get("state", {}).get("waiting", {}).get("reason", phase)
        return GradeResult(False, 0, 4, f"Pod api-app is not Ready (Phase: {phase}, reason: {waiting}); non-root user still cannot write to /data/cache subPath")
    restarts = ctx.get_pod_restart_count(pod)
    if restarts > 5:
        return GradeResult(False, 2, 4, f"Pod api-app is Ready but crashlooping ({restarts} restarts)")
    if restarts > 0:
        return GradeResult(False, 3, 4, f"Pod api-app is Ready but has {restarts} restarts; verify subPath permissions are stable")
    return GradeResult(True, 4, 4, "Pod api-app is 1/1 Running and stable with subPath writable by non-root user")
