from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pod = ctx.get_pod("restricted-runtime", "alpine-runner")
    if not pod:
        return GradeResult(False, 0, 3, "Pod alpine-runner not found in restricted-runtime")
    spec = pod.get("spec", {})
    users = [spec.get("securityContext", {}).get("runAsUser")]
    for c in spec.get("containers", []):
        users.append(c.get("securityContext", {}).get("runAsUser"))
    if 1000 not in users:
        return GradeResult(False, 0, 3, "runAsUser: 1000 missing from pod/container SecurityContext (image still runs as root with runAsNonRoot: true)")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        return GradeResult(False, 0, 3, f"runAsUser set but alpine-runner not Ready (Phase: {phase})")
    return GradeResult(True, 3, 3, "alpine-runner runs as UID 1000 and is 1/1 Ready")
