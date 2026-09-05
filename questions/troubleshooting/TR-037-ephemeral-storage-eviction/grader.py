from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("log-aggregator", "log-cruncher")
    if not pod:
        return GradeResult(False, 0, 4, "Pod log-cruncher not found in log-aggregator")
    res = pod.get("spec", {}).get("containers", [{}])[0].get("resources", {})
    req = res.get("requests", {}).get("ephemeral-storage")
    lim = res.get("limits", {}).get("ephemeral-storage")
    if req is None and lim is None:
        return GradeResult(False, 0, 4, "No ephemeral-storage request or limit set on log-cruncher")
    if req != "500Mi" or lim != "500Mi":
        return GradeResult(False, 2, 4, f"ephemeral-storage incomplete (request={req}, limit={lim}); both must be 500Mi")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        return GradeResult(False, 3, 4, f"Limits set but log-cruncher not Ready (Phase: {phase}, may still be evicted)")
    return GradeResult(True, 4, 4, "log-cruncher runs with ephemeral-storage request and limit of 500Mi")
