from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    res = ctx.run_cmd([
        "kubectl", "--context", ctx.context_name, "-n", "fintech",
        "auth", "can-i", "get", "secrets",
        "--as", "system:serviceaccount:fintech:vault-reader"
    ])
    if res.returncode != 0 or "yes" not in res.stdout.lower():
        return GradeResult(False, 0, 3, "vault-reader cannot get secrets in fintech")
    return GradeResult(True, 3, 3, "vault-reader has secret read permissions via RBAC")
