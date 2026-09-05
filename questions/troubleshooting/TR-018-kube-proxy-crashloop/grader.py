from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    pods = ctx.get_pods("kube-system", label_selector="k8s-app=kube-proxy")
    if not pods:
        return GradeResult(False, 0, 4, "No kube-proxy pods found in kube-system (label k8s-app=kube-proxy)")
    ready = [p for p in pods if ctx.check_pod_ready(p)]
    if not ready:
        return GradeResult(False, 0, 4, "All kube-proxy pods are not Ready; kube-proxy configuration is still invalid")
    crashlooping = [p["metadata"]["name"] for p in pods if ctx.get_pod_restart_count(p) > 5]
    if crashlooping:
        return GradeResult(False, 1, 4, "kube-proxy pods crashlooping: " + ", ".join(crashlooping))
    ds = ctx.get_resource("daemonset", "kube-proxy", "kube-system")
    if ds:
        desired = ds.get("status", {}).get("desiredNumberScheduled", 0)
        num_ready = ds.get("status", {}).get("numberReady", 0)
        if desired and num_ready < desired:
            return GradeResult(False, 2, 4, f"Only {num_ready}/{desired} kube-proxy pods Ready across nodes")
    return GradeResult(True, 4, 4, f"{len(ready)}/{len(pods)} kube-proxy pods Ready with no crashloops")
