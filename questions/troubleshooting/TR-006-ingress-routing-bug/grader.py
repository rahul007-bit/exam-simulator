from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    ing = ctx.get_ingress("gateway-ns", "api-gateway")
    if not ing:
        return GradeResult(False, 0, 3, "Ingress api-gateway not found")
    rules = ing.get("spec", {}).get("rules", [])
    if not rules or not rules[0].get("http", {}).get("paths"):
        return GradeResult(False, 0, 3, "No valid HTTP rules found in ingress")
    
    paths = {p.get("path"): p.get("backend", {}).get("service", {}).get("name") for p in rules[0]["http"]["paths"]}
    if paths.get("/orders") != "orders-svc" or paths.get("/users") != "users-svc":
        return GradeResult(False, 1, 3, f"Ingress routing paths incorrect: {paths}")
    return GradeResult(True, 3, 3, "Ingress routes paths correctly to orders-svc and users-svc")
