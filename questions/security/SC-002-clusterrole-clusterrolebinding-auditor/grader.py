from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(passed=False, score=0, max_score=3, message="Cluster unreachable via context k3d-cka", skipped=True)

    cr = ctx.get_resource("clusterrole", "cluster-auditor")
    if not cr:
        return GradeResult(False, 0, 3, "ClusterRole cluster-auditor not found")

    required = {"pods", "nodes", "services"}
    covered = set()
    for rule in cr.get("rules", []):
        if not any(g in ("", "*") for g in rule.get("apiGroups", [""])):
            continue
        verbs = set(rule.get("verbs", []))
        if not ({"get", "list", "watch"} <= verbs or "*" in verbs):
            continue
        covered |= {r for r in rule.get("resources", []) if r in required or r == "*"}
    if "*" not in covered and covered != required:
        return GradeResult(False, 0, 3, f"ClusterRole cluster-auditor rules incomplete: get/list/watch covered on {sorted(covered & required)}, need all of {sorted(required)}")

    for b in ctx.list_resources("clusterrolebinding"):
        if b.get("roleRef", {}).get("name") != "cluster-auditor":
            continue
        for s in b.get("subjects", []):
            if s.get("kind") == "User" and s.get("name") == "auditor-user":
                return GradeResult(True, 3, 3, f"ClusterRoleBinding {b['metadata']['name']} binds user auditor-user to cluster-auditor with read-only cluster access")

    return GradeResult(False, 1, 3, "ClusterRole cluster-auditor has correct rules but no ClusterRoleBinding binds user auditor-user to it")
