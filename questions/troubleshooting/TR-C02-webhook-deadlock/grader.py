from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("cluster-admissions", "recovery-app")
    if not pod:
        return GradeResult(passed=False, score=0, max_score=6, message="Pod recovery-app not found in cluster-admissions")
    if not ctx.check_pod_ready(pod):
        return GradeResult(passed=False, score=0, max_score=6, message="Pod recovery-app is not in Ready state")
    return GradeResult(passed=True, score=6, max_score=6, message="Admission webhook deadlock resolved and recovery-app running")
