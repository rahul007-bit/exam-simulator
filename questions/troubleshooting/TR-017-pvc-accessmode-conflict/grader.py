from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    pvc = ctx.get_pvc("media-platform", "shared-data")
    if not pvc:
        return GradeResult(False, 0, 3, "PVC shared-data not found in media-platform")
    phase = pvc.get("status", {}).get("phase")
    modes = pvc.get("spec", {}).get("accessModes", [])
    if phase != "Bound":
        return GradeResult(False, 0, 3, f"PVC shared-data is {phase}, expected Bound with ReadWriteOnce (current accessModes: {modes})")
    if "ReadWriteOnce" not in modes:
        return GradeResult(False, 1, 3, f"PVC shared-data is Bound but accessModes {modes} still lack ReadWriteOnce")
    return GradeResult(True, 3, 3, "PVC shared-data is Bound with ReadWriteOnce")
