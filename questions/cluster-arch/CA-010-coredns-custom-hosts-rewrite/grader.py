from core.graderlib import KubernetesContext, GradeResult

HOST_IP = "192.168.1.100"
HOST_NAME = "db.internal.company"

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    cm = ctx.get_configmap("kube-system", "coredns-custom")
    if not cm:
        return GradeResult(False, 0, 3, "ConfigMap coredns-custom not found in kube-system")
    score = 1
    entry_found = False
    for value in (cm.get("data") or {}).values():
        for line in value.splitlines():
            stripped = line.strip()
            if HOST_IP in stripped and HOST_NAME in stripped:
                entry_found = True
    if not entry_found:
        return GradeResult(False, 1, 3, f"coredns-custom ConfigMap lacks hosts entry mapping {HOST_NAME} to {HOST_IP}")
    return GradeResult(True, 3, 3, f"coredns-custom contains hosts entry {HOST_IP} {HOST_NAME}")
