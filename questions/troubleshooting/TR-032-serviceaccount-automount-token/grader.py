from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("order-auth", "api-client")
    if not pod:
        return GradeResult(False, 0, 3, "Pod api-client not found in order-auth")
    spec = pod.get("spec", {})
    if spec.get("automountServiceAccountToken") is False:
        return GradeResult(False, 0, 3, "automountServiceAccountToken is still explicitly false on pod api-client")
    vols = [v.get("name", "") for v in spec.get("volumes", [])]
    if not any(v.startswith("kube-api-access") for v in vols):
        return GradeResult(False, 0, 3, "No projected serviceaccount token volume (kube-api-access-*) mounted on api-client")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        return GradeResult(False, 0, 3, f"Token automounting fixed but api-client not Ready (Phase: {phase})")
    return GradeResult(True, 3, 3, "api-client automounts its serviceaccount token and is Ready")
