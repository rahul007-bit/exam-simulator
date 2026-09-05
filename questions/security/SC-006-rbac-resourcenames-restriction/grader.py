from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(passed=False, score=0, max_score=3, message="Cluster unreachable via context k3d-cka", skipped=True)

    role = ctx.get_resource("role", "vault-restricted", "rbac-fine-grained")
    if not role:
        return GradeResult(False, 0, 3, "Role vault-restricted not found in rbac-fine-grained")

    secret_rules = [r for r in role.get("rules", []) if "secrets" in r.get("resources", []) or "*" in r.get("resources", [])]
    if not secret_rules:
        return GradeResult(False, 0, 3, f"Role vault-restricted grants no access to secrets (rules: {role.get('rules')})")

    for r in secret_rules:
        verbs = set(r.get("verbs", []))
        rn = r.get("resourceNames", [])
        ok = (
            "get" in verbs
            and verbs <= {"get"}
            and set(r.get("resources", [])) == {"secrets"}
            and rn == ["allowed-creds"]
            and any(g in ("", "*") for g in r.get("apiGroups", [""]))
        )
        if not ok:
            return GradeResult(False, 1, 3, f"Role grants secrets access beyond get on allowed-creds only: verbs={r.get('verbs')}, resources={r.get('resources')}, resourceNames={rn} (want verbs=[get], resources=[secrets], resourceNames=[allowed-creds])")

    return GradeResult(True, 3, 3, "Role vault-restricted allows get only on Secret allowed-creds via resourceNames")
