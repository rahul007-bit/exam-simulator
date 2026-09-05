from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    pvc = ctx.get_pvc("data-storage", "app-pvc")
    if not pvc:
        return GradeResult(False, 0, 2, "PVC app-pvc not found in data-storage")
    if pvc.get("status", {}).get("phase") != "Bound":
        return GradeResult(False, 0, 2, f"PVC phase is {pvc.get('status',{}).get('phase')}, expected Bound")
    pv_name = pvc.get("spec", {}).get("volumeName")
    pv = ctx.get_pv(pv_name)
    if not pv or pv.get("status", {}).get("phase") != "Bound":
        return GradeResult(False, 1, 2, "PV is not Bound")
    return GradeResult(True, 2, 2, "PV and PVC bound successfully")
