from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    pdb = ctx.get_resource("pdb", "strict-pdb", "payment-processor")
    if not pdb:
        return GradeResult(False, 0, 4, "PDB strict-pdb not found in payment-processor")
    allowed = int(pdb.get("status", {}).get("disruptionsAllowed", 0) or 0)
    min_avail = pdb.get("spec", {}).get("minAvailable")
    max_unavail = pdb.get("spec", {}).get("maxUnavailable")
    sel = pdb.get("spec", {}).get("selector", {}).get("matchLabels", {}) or {}
    target = None
    for d in ctx.list_resources("deployment", "payment-processor"):
        if (d.get("spec", {}).get("selector", {}).get("matchLabels", {}) or {}) == sel:
            target = d
            break
    if target and ctx.deployment_ready_replicas(target) < 1:
        return GradeResult(False, 1, 4, "Deployment matching strict-pdb selector has 0 ready replicas")
    if allowed < 1:
        return GradeResult(False, 2, 4, f"PDB strict-pdb allows 0 disruptions (minAvailable: {min_avail}, maxUnavailable: {max_unavail}); drain still blocked")
    return GradeResult(True, 4, 4, f"PDB strict-pdb allows {allowed} disruption(s); node drain can proceed")
