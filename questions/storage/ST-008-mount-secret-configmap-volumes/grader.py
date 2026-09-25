from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("app-configs", "config-reader")
    if not pod:
        return GradeResult(False, 0, 3, "Pod config-reader not found in app-configs")
    volumes = pod.get("spec", {}).get("volumes", [])
    mounts = [m for c in pod.get("spec", {}).get("containers", []) for m in c.get("volumeMounts", [])]
    sec_vol = next((v["name"] for v in volumes if v.get("secret", {}).get("secretName") == "app-secret"), None)
    cm_vol = next((v["name"] for v in volumes if v.get("configMap", {}).get("name") == "app-config"), None)
    sec_mount = next((m for m in mounts if m.get("mountPath") == "/etc/secrets/token"), None)
    cm_mount = next((m for m in mounts if m.get("mountPath") == "/etc/config/app.conf"), None)
    if not ctx.get_secret("app-configs", "app-secret") or not sec_vol or not sec_mount or sec_mount.get("name") != sec_vol:
        return GradeResult(False, 0, 3, "Secret app-secret is not mounted at /etc/secrets/token in pod config-reader")
    if not ctx.get_configmap("app-configs", "app-config") or not cm_vol or not cm_mount or cm_mount.get("name") != cm_vol:
        return GradeResult(False, 1, 3, "ConfigMap app-config is not mounted at /etc/config/app.conf in pod config-reader")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 2, 3, "Secret and ConfigMap mounts configured but pod config-reader is not Running/Ready")
    return GradeResult(True, 3, 3, "Pod config-reader mounts app-secret and app-config at the target paths")
