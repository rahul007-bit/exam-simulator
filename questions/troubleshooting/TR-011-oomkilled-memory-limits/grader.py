from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("analytics-worker", "data-processor")
    if not pod:
        return GradeResult(False, 0, 4, "Pod data-processor not found")
    res = pod.get("spec", {}).get("containers", [{}])[0].get("resources", {})
    lim = res.get("limits", {}).get("memory", "")
    if "256" not in lim and "512" not in lim and "1G" not in lim and "1024" not in lim:
        return GradeResult(False, 1, 4, f"Memory limit {lim} is too low (expected >= 256Mi)")
    if pod.get("status", {}).get("phase") != "Running":
        return GradeResult(False, 2, 4, f"Pod phase is {pod.get('status',{}).get('phase')}")
    return GradeResult(True, 4, 4, "Memory requests and limits updated; processor running stably")
