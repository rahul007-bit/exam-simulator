from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(passed=False, score=0, max_score=3, message="Cluster unreachable via context k3d-cka", skipped=True)

    binding = ctx.get_resource("clusterrolebinding", "dev-ops-binding")
    if binding:
        role_ref = binding.get("roleRef", {}).get("name")
        subjects = [f"{s.get('kind')}:{s.get('name')}" for s in binding.get("subjects", [])]
        return GradeResult(False, 0, 3, f"ClusterRoleBinding dev-ops-binding still exists granting {role_ref} to {subjects} and must be deleted")

    remaining = {c["metadata"]["name"]: c.get("roleRef", {}).get("name") for c in ctx.list_resources("clusterrolebinding")}
    return GradeResult(True, 3, 3, f"ClusterRoleBinding dev-ops-binding deleted; remaining ClusterRoleBindings: {remaining}")
