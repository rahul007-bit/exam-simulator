from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(passed=False, score=0, max_score=6, message="Cluster unreachable via context k3d-cka", skipped=True)

    sas = [s["metadata"]["name"] for s in ctx.list_resources("serviceaccount", "operator-core") if s["metadata"]["name"] != "default"]
    if not sas:
        return GradeResult(False, 0, 6, "No operator ServiceAccount found in operator-core")

    able = []
    for sa in sas:
        res = ctx.run_cmd([
            "kubectl", "--context", ctx.context_name, "-n", "operator-core",
            "auth", "can-i", "create", "rolebindings.rbac.authorization.k8s.io",
            "--as", f"system:serviceaccount:operator-core:{sa}",
        ])
        if res.returncode == 0 and "yes" in res.stdout.lower():
            able.append(sa)
    if not able:
        return GradeResult(False, 0, 6, f"Intermediated permissions not granted: no ServiceAccount in operator-core can create rolebindings (checked: {sas})")

    bindings = ctx.list_resources("rolebinding", "operator-core")
    if not bindings:
        return GradeResult(False, 3, 6, f"Operator {able[0]} can now create rolebindings but no RoleBinding was created in operator-core")

    names = [b["metadata"]["name"] for b in bindings]
    return GradeResult(True, 6, 6, f"Operator {able[0]} can create rolebindings and RoleBinding(s) {names} exist in operator-core")
