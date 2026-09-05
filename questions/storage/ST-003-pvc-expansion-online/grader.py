from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pvc = ctx.get_pvc("media-store", "data-vol")
    if not pvc:
        return GradeResult(False, 0, 3, "PVC data-vol not found in media-store")
    if pvc.get("status", {}).get("phase") != "Bound":
        return GradeResult(False, 0, 3, f"PVC data-vol phase is {pvc.get('status', {}).get('phase')}, expected Bound")
    score = 1
    req = pvc.get("spec", {}).get("resources", {}).get("requests", {}).get("storage")
    if req != "3Gi":
        return GradeResult(False, score, 3, f"PVC data-vol storage request is {req}, expected 3Gi")
    score = 2
    pods = [p for p in ctx.get_pods("media-store") if any(v.get("persistentVolumeClaim", {}).get("claimName") == "data-vol" for v in p.get("spec", {}).get("volumes", []))]
    if not pods:
        return GradeResult(False, score, 3, "PVC expanded to 3Gi but no pod attached to data-vol was found (attached pod must not be deleted)")
    return GradeResult(True, 3, 3, "PVC data-vol expanded to 3Gi with the attached pod still running")
