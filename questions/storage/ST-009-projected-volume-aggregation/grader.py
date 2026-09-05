from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("app-credentials", "projected-pod")
    if not pod:
        return GradeResult(False, 0, 2, "Pod projected-pod not found in app-credentials")
    proj = next((v.get("projected", {}) for v in pod.get("spec", {}).get("volumes", []) if v.get("projected")), None)
    if not proj:
        return GradeResult(False, 0, 2, "Pod projected-pod has no projected volume")
    sources = proj.get("sources", [])
    if not any(s.get("secret", {}).get("name") == "vault-creds" for s in sources):
        return GradeResult(False, 0, 2, "Projected volume does not include Secret vault-creds")
    downward = next((s.get("downwardAPI") for s in sources if s.get("downwardAPI")), None)
    fields = [i.get("fieldRef", {}).get("fieldPath") for i in (downward or {}).get("items", [])]
    if "metadata.name" not in fields or "metadata.namespace" not in fields:
        return GradeResult(False, 1, 2, "Projected volume downwardAPI must expose metadata.name and metadata.namespace")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 1, 2, "Projected volume configured but pod projected-pod is not Running/Ready")
    return GradeResult(True, 2, 2, "Pod projected-pod aggregates vault-creds secret and downwardAPI pod name/namespace")
