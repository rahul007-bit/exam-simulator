from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    svc = ctx.get_service("external-routing", "db-external")
    if not svc:
        return GradeResult(False, 0, 3, "Service db-external not found in external-routing")
    if svc.get("spec", {}).get("type") != "ExternalName":
        return GradeResult(False, 0, 3, "Service db-external is not of type ExternalName")
    target = svc.get("spec", {}).get("externalName", "")
    if target != "db.prod.internal.corp":
        return GradeResult(False, 0, 3, f"externalName is {target!r}, expected db.prod.internal.corp")
    return GradeResult(True, 3, 3, f"db-external correctly targets {target}")
