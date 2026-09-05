from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    res = ctx.run_cmd([
        "kubectl", "--context", ctx.context_name, "-n", "billing-app",
        "auth", "can-i", "create", "deployments.apps",
        "--as", "system:serviceaccount:billing-app:app-deployer"
    ])
    if res.returncode != 0 or "yes" not in res.stdout.lower():
        return GradeResult(passed=False, score=0, max_score=2, message="ServiceAccount cannot create deployments in billing-app")
    
    res_del = ctx.run_cmd([
        "kubectl", "--context", ctx.context_name, "-n", "billing-app",
        "auth", "can-i", "delete", "deployments.apps",
        "--as", "system:serviceaccount:billing-app:app-deployer"
    ])
    if res_del.returncode != 0 or "yes" not in res_del.stdout.lower():
        return GradeResult(passed=False, score=1, max_score=2, message="ServiceAccount missing delete permission on deployments")
        
    return GradeResult(passed=True, score=2, max_score=2, message="RBAC ServiceAccount and RoleBinding configured properly")
