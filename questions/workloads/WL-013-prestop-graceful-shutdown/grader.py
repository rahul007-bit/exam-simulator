from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("graceful-shutdown", "graceful-app")
    if not pod:
        return GradeResult(False, 0, 3, "Pod graceful-app not found in graceful-shutdown")
    hook = None
    for c in pod.get("spec", {}).get("containers", []):
        h = c.get("lifecycle", {}).get("preStop", {})
        if h:
            hook = h
            break
    if not hook or not hook.get("exec"):
        return GradeResult(False, 0, 3, "Pod graceful-app has no preStop exec hook")
    cmd = hook.get("exec", {}).get("command", [])
    if cmd != ["/bin/sh", "-c", "sleep 15; nginx -s quit"]:
        return GradeResult(False, 1, 3, f"preStop command is {cmd}, expected ['/bin/sh', '-c', 'sleep 15; nginx -s quit']")
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, 2, 3, "preStop hook configured but pod graceful-app is not Running/Ready")
    return GradeResult(True, 3, 3, "Pod graceful-app has the correct preStop exec hook configured")
