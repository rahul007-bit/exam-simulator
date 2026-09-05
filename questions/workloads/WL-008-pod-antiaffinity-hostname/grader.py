from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    dep = ctx.get_deployment("resilient-app", "spread-web")
    if not dep:
        return GradeResult(False, 0, 3, "Deployment spread-web not found in resilient-app")
    spec = dep.get("spec", {})
    if spec.get("replicas") != 2:
        return GradeResult(False, 0, 3, f"Deployment spread-web replicas={spec.get('replicas')}, expected 2")
    pa = spec.get("template", {}).get("spec", {}).get("affinity", {}).get("podAntiAffinity", {})
    terms = pa.get("requiredDuringSchedulingIgnoredDuringExecution", []) + [i.get("podAffinityTerm", {}) for i in pa.get("preferredDuringSchedulingIgnoredDuringExecution", [])]
    if not any(t.get("topologyKey") == "kubernetes.io/hostname" for t in terms):
        return GradeResult(False, 0, 3, "Deployment spread-web has no podAntiAffinity with topologyKey kubernetes.io/hostname")
    if dep.get("status", {}).get("readyReplicas") != 2:
        return GradeResult(False, 1, 3, f"Deployment spread-web has {dep.get('status', {}).get('readyReplicas')} ready replicas, expected 2")
    sel = ",".join(f"{k}={v}" for k, v in spec.get("selector", {}).get("matchLabels", {}).items())
    pods = [p for p in ctx.get_pods("resilient-app", sel) if p.get("status", {}).get("phase") == "Running"]
    nodes = {p.get("spec", {}).get("nodeName") for p in pods}
    if len(nodes) < 2 and len(ctx.get_nodes()) >= 2:
        return GradeResult(False, 2, 3, f"Running replicas are on nodes {nodes}, expected one per node")
    return GradeResult(True, 3, 3, "Deployment spread-web runs 2 replicas on separate nodes via podAntiAffinity")
