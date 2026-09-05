from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pvc = ctx.get_pvc("data-ops", "data-claim")
    if not pvc:
        return GradeResult(passed=False, score=0, max_score=3, message="PVC data-claim not found in data-ops")
    phase = pvc.get("status", {}).get("phase")
    if phase != "Bound":
        return GradeResult(passed=False, score=0, max_score=3, message=f"PVC data-claim is in phase '{phase}', expected 'Bound'")
    return GradeResult(passed=True, score=3, max_score=3, message="PVC data-claim is successfully Bound")
