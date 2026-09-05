from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    svc = ctx.get_service("db-cluster", "cassandra-svc")
    if not svc:
        return GradeResult(False, 0, 3, "Service cassandra-svc not found in db-cluster")
    cluster_ip = svc.get("spec", {}).get("clusterIP")
    if cluster_ip != "None":
        return GradeResult(False, 0, 3, f"Service cassandra-svc has clusterIP {cluster_ip}, expected None so cassandra-cluster peers resolve via headless DNS")
    return GradeResult(True, 3, 3, "cassandra-svc is headless (clusterIP: None), StatefulSet peer DNS discovery works")
