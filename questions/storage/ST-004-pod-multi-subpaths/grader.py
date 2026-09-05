from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("subpath-multi", "multi-subpath")
    if not pod:
        return GradeResult(False, 0, 3, "Pod multi-subpath not found in subpath-multi")
    vol_names = [v.get("name") for v in pod.get("spec", {}).get("volumes", [])]
    if "data-storage" not in vol_names:
        return GradeResult(False, 0, 3, "Pod multi-subpath does not define a volume named data-storage")
    mounts = [m for c in pod.get("spec", {}).get("containers", []) for m in c.get("volumeMounts", [])]
    cfg = next((m for m in mounts if m.get("mountPath") == "/app/config"), None)
    logs = next((m for m in mounts if m.get("mountPath") == "/app/logs"), None)
    if not cfg or cfg.get("subPath") != "config" or (cfg.get("name") != "data-storage" and cfg.get("volumeName") != "data-storage"):
        return GradeResult(False, 1, 3, f"VolumeMount for /app/config must use volume data-storage with subPath config (got {cfg})")
    if not logs or logs.get("subPath") != "logs" or (logs.get("name") != "data-storage" and logs.get("volumeName") != "data-storage"):
        return GradeResult(False, 2, 3, f"VolumeMount for /app/logs must use volume data-storage with subPath logs (got {logs})")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 2, 3, "SubPath mounts configured but pod multi-subpath is not Running/Ready")
    return GradeResult(True, 3, 3, "Pod multi-subpath mounts volume data-storage at /app/config and /app/logs via subPaths")
