from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    dep = ctx.get_deployment("shipping", "delivery-service")
    if not dep:
        return GradeResult(False, 0, 3, "Deployment delivery-service not found in shipping")

    containers = dep.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
    image = containers[0].get("image", "") if containers else ""
    if "broken" in image:
        return GradeResult(False, 0, 3, f"Deployment is still on failed revision with broken image: {image}")

    status = dep.get("status", {})
    ready = status.get("readyReplicas", 0)
    updated = status.get("updatedReplicas", 0)
    replicas = status.get("replicas", 0)
    if ready < 2 or updated < 2 or replicas != 2:
        return GradeResult(False, 1, 3, f"Deployment not fully healthy: ready={ready}/2, updated={updated}/2")

    return GradeResult(True, 3, 3, "Delivery service successfully rolled back to working revision with 2/2 ready pods")
