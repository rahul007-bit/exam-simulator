from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("net-tools", "net-monitor")
    if not pod:
        return GradeResult(False, 0, 3, "Pod net-monitor not found in net-tools")
    c_sc = pod.get("spec", {}).get("containers", [{}])[0].get("securityContext", {})
    caps = c_sc.get("capabilities", {})
    drop = caps.get("drop", [])
    add = caps.get("add", [])
    if "ALL" not in drop or "NET_ADMIN" not in add:
        return GradeResult(False, 1, 3, f"Capabilities mismatch: drop={drop}, add={add}")
    return GradeResult(True, 3, 3, "Capabilities configured with drop ALL and add NET_ADMIN")
