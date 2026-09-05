from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    data = ctx.kubectl(["get", "hpa", "web-scaler"], namespace="customer-portal")
    if not data:
        return GradeResult(False, 0, 3, "HPA web-scaler not found in customer-portal")
    spec = data.get("spec", {})
    if spec.get("minReplicas") != 2 or spec.get("maxReplicas") != 8:
        return GradeResult(False, 1, 3, f"HPA min/max replicas incorrect: min={spec.get('minReplicas')}, max={spec.get('maxReplicas')}")

    target_cpu = spec.get("targetCPUUtilizationPercentage")
    if target_cpu is None:
        metrics = spec.get("metrics", [])
        for m in metrics:
            if m.get("type") == "Resource" and m.get("resource", {}).get("name") == "cpu":
                target_cpu = m.get("resource", {}).get("target", {}).get("averageUtilization")

    if target_cpu != 60:
        return GradeResult(False, 2, 3, f"HPA target CPU utilization is {target_cpu}%, expected 60%")

    return GradeResult(True, 3, 3, "HPA web-scaler configured properly targeting 60% CPU (min=2, max=8)")
