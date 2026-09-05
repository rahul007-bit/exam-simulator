from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    ing = ctx.get_ingress("edge-routing", "app-ingress")
    if not ing:
        return GradeResult(False, 0, 2, "Ingress app-ingress not found in edge-routing")
    rules = ing.get("spec", {}).get("rules", [])
    if not rules or not rules[0].get("http", {}).get("paths"):
        return GradeResult(False, 0, 2, "No paths defined in ingress rules")
    paths = {p.get("path"): p.get("backend", {}).get("service", {}).get("name") for p in rules[0]["http"]["paths"]}
    if paths.get("/auth") != "auth-svc" or paths.get("/pay") != "pay-svc":
        return GradeResult(False, 1, 2, f"Path routing mismatch: {paths}")
    return GradeResult(True, 2, 2, "Ingress routing configured properly")
