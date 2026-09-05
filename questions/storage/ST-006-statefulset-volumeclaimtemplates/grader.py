from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    sts = ctx.get_resource("statefulset", "redis-cluster", "redis-cluster")
    if not sts:
        return GradeResult(False, 0, 3, "StatefulSet redis-cluster not found in redis-cluster")
    spec = sts.get("spec", {})
    vcts = spec.get("volumeClaimTemplates", [])
    if not vcts:
        return GradeResult(False, 0, 3, "StatefulSet redis-cluster has no volumeClaimTemplates")
    vct = vcts[0]
    name = vct.get("metadata", {}).get("name")
    req = vct.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
    sc = vct.get("spec", {}).get("storageClassName")
    if spec.get("replicas") != 2 or req != "1Gi" or sc != "local-path":
        return GradeResult(False, 0, 3, f"StatefulSet spec wrong: replicas={spec.get('replicas')}, claim request={req}, storageClassName={sc}")
    if sts.get("status", {}).get("readyReplicas") != 2:
        return GradeResult(False, 1, 3, f"StatefulSet redis-cluster has {sts.get('status', {}).get('readyReplicas')} ready replicas, expected 2")
    for i in range(2):
        pvc = ctx.get_pvc("redis-cluster", f"{name}-redis-cluster-{i}")
        if not pvc:
            return GradeResult(False, 2, 3, f"PVC {name}-redis-cluster-{i} not found in redis-cluster")
        if pvc.get("status", {}).get("phase") != "Bound":
            return GradeResult(False, 2, 3, f"PVC {name}-redis-cluster-{i} phase is {pvc.get('status', {}).get('phase')}, expected Bound")
    return GradeResult(True, 3, 3, "StatefulSet redis-cluster is ready with both per-ordinal PVCs Bound")
