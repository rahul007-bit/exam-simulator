from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    pv = ctx.get_pv("backup-data-pv")
    if not pv:
        return GradeResult(False, 0, 4, "PersistentVolume backup-data-pv not found")
    phase = pv.get("status", {}).get("phase")
    cr = pv.get("spec", {}).get("claimRef")
    if phase == "Available":
        return GradeResult(True, 4, 4, "PV backup-data-pv is Available for rebinding after claimRef cleanup")
    cleared = not cr or not cr.get("uid")
    if cleared:
        return GradeResult(False, 2, 4, f"PV backup-data-pv claimRef is cleared but phase is {phase}, expected Available")
    return GradeResult(False, 1, 4, f"PV backup-data-pv is still {phase} with claimRef to {cr.get('namespace')}/{cr.get('name')} (uid still set)")
