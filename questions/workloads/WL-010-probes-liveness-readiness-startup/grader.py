from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("health-monitoring", "health-app")
    if not pod:
        return GradeResult(False, 0, 3, "Pod health-app not found in health-monitoring")
    container = next((c for c in pod.get("spec", {}).get("containers", []) if c.get("startupProbe") and c.get("readinessProbe") and c.get("livenessProbe")), None)
    if not container:
        return GradeResult(False, 0, 3, "Pod health-app has no container with startup, readiness, and liveness probes")
    sp = container.get("startupProbe", {})
    if sp.get("periodSeconds") != 5 or sp.get("failureThreshold") != 10:
        return GradeResult(False, 1, 3, f"startupProbe wrong: periodSeconds={sp.get('periodSeconds')} (expected 5), failureThreshold={sp.get('failureThreshold')} (expected 10)")
    rp = container.get("readinessProbe", {}).get("httpGet", {}).get("path")
    if rp != "/ready":
        return GradeResult(False, 1, 3, f"readinessProbe httpGet path is {rp}, expected /ready")
    lp = container.get("livenessProbe", {}).get("httpGet", {}).get("path")
    if lp != "/health":
        return GradeResult(False, 2, 3, f"livenessProbe httpGet path is {lp}, expected /health")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 2, 3, "Probes configured but pod health-app is not Running/Ready")
    return GradeResult(True, 3, 3, "Pod health-app has startup (5s/10), readiness (/ready), and liveness (/health) probes")
