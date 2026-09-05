from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pods = ctx.get_pods("geo-distribution", "app=zone-spread-app")
    if not pods:
        return GradeResult(False, 0, 3, "No zone-spread-app pods found")
    
    ready_count = sum(1 for p in pods if ctx.check_pod_ready(p))
    if ready_count < 4:
        return GradeResult(False, ready_count, 3, f"Only {ready_count}/4 pods are Ready")
    
    return GradeResult(True, 3, 3, "All 4 zone-spread-app pods scheduled and running")
