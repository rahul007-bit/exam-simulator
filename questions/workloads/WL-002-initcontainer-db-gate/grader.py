from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("frontend-ui", "web-app")
    if not pod:
        return GradeResult(False, 0, 2, "Pod web-app not found in frontend-ui")
    init_c = pod.get("spec", {}).get("initContainers", [])
    if not init_c or init_c[0].get("name") != "wait-for-db":
        return GradeResult(False, 0, 2, "InitContainer wait-for-db not found")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 1, 2, "Pod is not in Ready state")
    return GradeResult(True, 2, 2, "Pod web-app successfully initialized and running")
