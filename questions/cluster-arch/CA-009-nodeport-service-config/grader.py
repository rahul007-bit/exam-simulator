from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    svc = ctx.get_service("external-services", "web-nodeport")
    if not svc:
        return GradeResult(False, 0, 2, "Service web-nodeport not found in external-services")
    if svc.get("spec", {}).get("type") != "NodePort":
        return GradeResult(False, 0, 2, f"Service type is {svc.get('spec',{}).get('type')}, expected NodePort")
    ports = svc.get("spec", {}).get("ports", [])
    if not any(p.get("nodePort") == 30080 for p in ports):
        return GradeResult(False, 1, 2, "nodePort is not set to 30080")
    return GradeResult(True, 2, 2, "NodePort service configured on port 30080")
