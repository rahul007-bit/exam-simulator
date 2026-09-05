from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    dep = ctx.get_deployment("api-gateway", "api-server")
    if not dep:
        return GradeResult(False, 0, 3, "Deployment api-server not found in api-gateway")
    containers = dep.get("spec", {}).get("template", {}).get("spec", {}).get("containers", []) or []
    missing = [c.get("name") for c in containers if not (c.get("resources", {}).get("requests", {}) or {}).get("cpu")]
    if missing:
        return GradeResult(False, 0, 3, "Container(s) " + ", ".join(str(m) for m in missing) + " in api-server still define no CPU requests; HPA api-scaler reports <unknown>/50%")
    return GradeResult(True, 3, 3, "All api-server containers define CPU requests; HPA api-scaler can compute utilization")
