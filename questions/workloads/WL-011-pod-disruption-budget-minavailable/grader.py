from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pdb = ctx.get_resource("pdb", "web-pdb", "web-application")
    if not pdb:
        return GradeResult(False, 0, 3, "PDB web-pdb not found in web-application")
    spec = pdb.get("spec", {})
    if spec.get("minAvailable") != 2:
        return GradeResult(False, 0, 3, f"PDB web-pdb minAvailable is {spec.get('minAvailable')}, expected 2")
    if spec.get("selector", {}).get("matchLabels", {}).get("app") != "web-app":
        return GradeResult(False, 1, 3, f"PDB web-pdb selector is {spec.get('selector')}, expected app=web-app")
    status = pdb.get("status", {})
    expected = status.get("expectedPods", 0)
    healthy = status.get("currentHealthy", 0)
    if expected >= 1 and healthy < 2:
        return GradeResult(False, 2, 3, f"PDB status: expectedPods={expected}, currentHealthy={healthy}, need at least 2 healthy pods")
    return GradeResult(True, 3, 3, f"PDB web-pdb has minAvailable 2 targeting app=web-app with {healthy} healthy pods")
