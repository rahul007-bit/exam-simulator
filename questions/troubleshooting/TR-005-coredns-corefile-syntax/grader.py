from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pods = ctx.get_pods("kube-system", label_selector="k8s-app=kube-dns")
    if not pods:
        return GradeResult(False, 0, 3, "No CoreDNS pods found")
    ready_count = sum(1 for p in pods if ctx.check_pod_ready(p))
    if ready_count < len(pods) or ready_count == 0:
        return GradeResult(False, 0, 3, f"CoreDNS ready pods: {ready_count}/{len(pods)}")
    return GradeResult(True, 3, 3, "CoreDNS cluster DNS is fully operational")
