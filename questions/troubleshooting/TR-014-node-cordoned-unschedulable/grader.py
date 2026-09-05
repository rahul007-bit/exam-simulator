from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    dep = ctx.get_deployment("prod-workers", "worker-pool")
    if not dep:
        return GradeResult(False, 0, 3, "Deployment worker-pool not found in prod-workers")
    nodes = ctx.get_nodes()
    cordoned = [n["metadata"]["name"] for n in nodes if n.get("spec", {}).get("unschedulable")]
    if cordoned:
        return GradeResult(False, 0, 3, "Node(s) still cordoned: " + ", ".join(cordoned))
    ready = ctx.deployment_ready_replicas(dep)
    desired = dep.get("spec", {}).get("replicas", 0)
    if ready < 3:
        return GradeResult(False, 1, 3, f"worker-pool has {ready}/{desired} ready replicas, expected 3 (node schedulability fixed but pods not scheduled)")
    return GradeResult(True, 3, 3, "All nodes are schedulable and worker-pool has 3/3 ready replicas")
