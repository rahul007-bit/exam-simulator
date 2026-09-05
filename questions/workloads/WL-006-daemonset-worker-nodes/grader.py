from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    ds = ctx.get_resource("daemonset", "system-monitor", "node-monitoring")
    if not ds:
        return GradeResult(False, 0, 3, "DaemonSet system-monitor not found in node-monitoring")
    status = ds.get("status", {})
    desired = status.get("desiredNumberScheduled", 0)
    scheduled = status.get("currentNumberScheduled") if status.get("currentNumberScheduled") is not None else status.get("numberScheduled")
    ready = status.get("numberReady", 0)
    if desired < 1 or desired != scheduled or desired != ready:
        return GradeResult(False, 1, 3, f"DaemonSet status: desired={desired}, scheduled={scheduled}, ready={ready}")
    score = 2
    images = [c.get("image") for c in ds.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])]
    if "nginx:alpine" not in images:
        return GradeResult(False, score, 3, f"DaemonSet container images are {images}, expected nginx:alpine")
    workers = [n for n in ctx.get_nodes() if "node-role.kubernetes.io/control-plane" not in n.get("metadata", {}).get("labels", {})]
    if workers and desired != len(workers):
        return GradeResult(False, score, 3, f"DaemonSet desired={desired} but cluster has {len(workers)} worker nodes")
    return GradeResult(True, 3, 3, f"DaemonSet system-monitor runs nginx:alpine on all {desired} worker nodes")
