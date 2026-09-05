from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    sts = ctx.get_resource("statefulset", "cache-node", "stateful-db")
    if not sts:
        return GradeResult(False, 0, 3, "StatefulSet cache-node not found in stateful-db")
    policy = sts.get("spec", {}).get("persistentVolumeClaimRetentionPolicy", {})
    if policy.get("whenDeleted") != "Delete":
        current = policy.get("whenDeleted", "Retain (default)")
        return GradeResult(False, 0, 3, f"persistentVolumeClaimRetentionPolicy.whenDeleted is {current!r}, expected Delete")
    ready = int(sts.get("status", {}).get("readyReplicas", 0) or 0)
    wanted = int(sts.get("spec", {}).get("replicas", 1) or 1)
    if ready < wanted:
        return GradeResult(False, 0, 3, f"Retention policy set but cache-node not Ready: {ready}/{wanted} replicas")
    return GradeResult(True, 3, 3, "cache-node uses whenDeleted: Delete retention policy and is fully Ready")
