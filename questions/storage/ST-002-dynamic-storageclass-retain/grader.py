from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    data = ctx.kubectl(["get", "sc", "fast-retain"])
    if not data:
        return GradeResult(False, 0, 3, "StorageClass fast-retain not found")
    if data.get("reclaimPolicy") != "Retain":
        return GradeResult(False, 1, 3, f"reclaimPolicy is {data.get('reclaimPolicy')}, expected Retain")
    if data.get("volumeBindingMode") != "WaitForFirstConsumer":
        return GradeResult(False, 1, 3, f"volumeBindingMode is {data.get('volumeBindingMode')}, expected WaitForFirstConsumer")
    return GradeResult(True, 3, 3, "StorageClass fast-retain is configured properly")
