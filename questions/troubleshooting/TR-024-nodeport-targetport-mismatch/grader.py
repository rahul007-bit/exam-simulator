from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    svc = ctx.get_service("web-services", "web-svc")
    if not svc:
        return GradeResult(False, 0, 3, "Service web-svc not found in web-services")
    ports = svc.get("spec", {}).get("ports", []) or []
    if not any(str(p.get("targetPort")) == "80" for p in ports):
        target_ports = [p.get("targetPort") for p in ports]
        return GradeResult(False, 0, 3, f"Service web-svc forwards to targetPort(s) {target_ports}, expected 80 (containerPort)")
    return GradeResult(True, 3, 3, "Service web-svc routes NodePort traffic to targetPort 80")
