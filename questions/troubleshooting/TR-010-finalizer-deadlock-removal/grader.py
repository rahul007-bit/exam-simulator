from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    cm = ctx.get_configmap("legacy-services", "legacy-vault")
    if cm:
        return GradeResult(False, 0, 2, "ConfigMap legacy-vault is still present / terminating")
    return GradeResult(True, 2, 2, "Finalizer successfully cleared and resource deleted")
