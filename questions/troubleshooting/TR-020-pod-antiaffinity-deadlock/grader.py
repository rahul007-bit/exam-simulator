from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    dep = ctx.get_deployment("web-tier", "web-redundant")
    if not dep:
        return GradeResult(False, 0, 4, "Deployment web-redundant not found in web-tier")
    paa = dep.get("spec", {}).get("template", {}).get("spec", {}).get("affinity", {}).get("podAntiAffinity", {})
    hard = "requiredDuringSchedulingIgnoredDuringExecution" in paa
    ready = ctx.deployment_ready_replicas(dep)
    if hard:
        if ready >= 4:
            return GradeResult(False, 2, 4, "web-redundant has 4/4 ready replicas but hard podAntiAffinity (requiredDuringScheduling) is still present")
        return GradeResult(False, 0, 4, f"Hard podAntiAffinity still present; only {ready}/4 replicas schedulable, convert to preferredDuringScheduling")
    if ready < 4:
        return GradeResult(False, 2, 4, f"Soft affinity configured but web-redundant has {ready}/4 ready replicas, expected 4")
    return GradeResult(True, 4, 4, "web-redundant uses soft podAntiAffinity and runs 4/4 ready replicas")
