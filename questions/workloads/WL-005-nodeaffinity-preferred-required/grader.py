from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("web-cluster", "affinity-pod")
    if not pod:
        return GradeResult(False, 0, 3, "Pod affinity-pod not found in web-cluster")
    na = pod.get("spec", {}).get("affinity", {}).get("nodeAffinity", {})
    req = na.get("requiredDuringSchedulingIgnoredDuringExecution", {}).get("nodeSelectorTerms", [])
    req_ok = any(any(e.get("key") == "topology.kubernetes.io/zone" and e.get("operator") == "In" and "zone-1" in e.get("values", []) for e in t.get("matchExpressions", [])) for t in req)
    if not req_ok:
        return GradeResult(False, 0, 3, "nodeAffinity required rule does not match topology.kubernetes.io/zone In (zone-1)")
    pref = na.get("preferredDuringSchedulingIgnoredDuringExecution", [])
    pref_ok = any(any(e.get("key") == "disk" and e.get("operator") == "In" and "ssd" in e.get("values", []) for e in i.get("preference", {}).get("matchExpressions", [])) for i in pref)
    if not pref_ok:
        return GradeResult(False, 1, 3, "nodeAffinity preferred rule does not match disk In (ssd)")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 2, 3, "nodeAffinity rules configured but pod affinity-pod is not Running/Ready")
    return GradeResult(True, 3, 3, "Pod affinity-pod has required zone-1 and preferred ssd nodeAffinity rules")
