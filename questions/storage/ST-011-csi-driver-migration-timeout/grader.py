from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("db-storage", "db-replica")
    if not pod:
        return GradeResult(False, 0, 4, "Pod db-replica not found in db-storage")
    score = 1
    stuck = [va["metadata"]["name"] for va in ctx.list_resources("volumeattachment") if va.get("status", {}).get("attached") is False]
    if pod.get("status", {}).get("phase") != "Running":
        if stuck:
            return GradeResult(False, score, 4, f"Pod db-replica is {pod.get('status', {}).get('phase')}; stale VolumeAttachment still present: {', '.join(stuck)}")
        return GradeResult(False, score, 4, f"Pod db-replica phase is {pod.get('status', {}).get('phase')}, expected Running")
    score = 3
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, score, 4, "Pod db-replica is Running but its containers are not Ready")
    return GradeResult(True, 4, 4, "Stale VolumeAttachment cleared and pod db-replica is Running/Ready")
