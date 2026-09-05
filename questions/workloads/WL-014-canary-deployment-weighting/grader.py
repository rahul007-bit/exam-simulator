from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    v1 = ctx.get_deployment("traffic-canary", "app-v1")
    canary = ctx.get_deployment("traffic-canary", "app-canary")
    if not v1:
        return GradeResult(False, 0, 4, "Deployment app-v1 not found in traffic-canary")
    if v1.get("spec", {}).get("replicas") != 3 or ctx.deployment_ready_replicas(v1) != 3:
        return GradeResult(False, 0, 4, f"app-v1 must have 3 ready replicas (ready={ctx.deployment_ready_replicas(v1)})")
    if not canary:
        return GradeResult(False, 1, 4, "Deployment app-canary not found in traffic-canary")
    if canary.get("spec", {}).get("replicas") != 1 or ctx.deployment_ready_replicas(canary) != 1:
        return GradeResult(False, 1, 4, f"app-canary must have 1 ready replica (ready={ctx.deployment_ready_replicas(canary)})")
    svc = ctx.get_service("traffic-canary", "app-svc")
    if not svc:
        return GradeResult(False, 2, 4, "Service app-svc not found in traffic-canary")
    ports = [p.get("port") for p in svc.get("spec", {}).get("ports", [])]
    if 80 not in ports:
        return GradeResult(False, 2, 4, f"Service app-svc ports are {ports}, expected port 80")

    def sel(d):
        return ",".join(f"{k}={v}" for k, v in d.get("spec", {}).get("selector", {}).get("matchLabels", {}).items())
    ep = ctx.get_endpoints("traffic-canary", "app-svc")
    ep_ips = {a.get("ip") for s in (ep or {}).get("subsets", []) for a in s.get("addresses", []) or []}
    ips_v1 = {p.get("status", {}).get("podIP") for p in ctx.get_pods("traffic-canary", sel(v1))}
    ips_canary = {p.get("status", {}).get("podIP") for p in ctx.get_pods("traffic-canary", sel(canary))}
    if not (ep_ips & ips_v1) or not (ep_ips & ips_canary):
        return GradeResult(False, 3, 4, "Service app-svc endpoints do not include pods from both app-v1 and app-canary")
    return GradeResult(True, 4, 4, "Service app-svc on port 80 routes to app-v1 (3 replicas) and app-canary (1 replica)")
