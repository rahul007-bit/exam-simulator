from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pvc = ctx.get_pvc("exclusive-storage", "exclusive-claim")
    if not pvc:
        return GradeResult(False, 0, 3, "PVC exclusive-claim not found in exclusive-storage")
    modes = pvc.get("spec", {}).get("accessModes", [])
    if "ReadWriteOncePod" not in modes:
        return GradeResult(False, 0, 3, f"PVC exclusive-claim accessModes is {modes}, expected ReadWriteOncePod")
    score = 1
    req = pvc.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
    if req != "1Gi":
        return GradeResult(False, score, 3, f"PVC exclusive-claim storage request is {req}, expected 1Gi")
    score = 2
    phase = pvc.get("status", {}).get("phase")
    if phase != "Bound":
        return GradeResult(False, score, 3, f"PVC exclusive-claim phase is {phase}, expected Bound")
    return GradeResult(True, 3, 3, "PVC exclusive-claim uses ReadWriteOncePod with 1Gi and is Bound")
