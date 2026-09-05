from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    pods = ctx.get_pods("compute-pool")
    if len(pods) < 5:
        return GradeResult(False, 0, 6, f"Expected 5 pods in compute-pool, found {len(pods)}")
    ready = [p for p in pods if ctx.check_pod_ready(p)]
    if len(ready) < 5:
        stuck = [p.get("metadata", {}).get("name") for p in pods if not ctx.check_pod_ready(p)]
        score = min(len(ready) * 6 // 5, 6)
        return GradeResult(False, score, 6, f"Only {len(ready)}/5 pods Running; still unschedulable: {', '.join(stuck)}")
    return GradeResult(True, 6, 6, "All 5 compute-pool pods scheduled and Running after untangling affinity, taints and anti-affinity")
