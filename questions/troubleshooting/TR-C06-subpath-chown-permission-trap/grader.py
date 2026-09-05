from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    pods = ctx.get_pods("database-tier")
    if not pods:
        return GradeResult(False, 0, 6, "No pods found in database-tier")
    pod = pods[0]
    name = pod.get("metadata", {}).get("name")
    if not pod.get("spec", {}).get("initContainers"):
        return GradeResult(False, 0, 6, f"Pod {name} has no initContainer chown fix for the root-owned /data/db subPath directory")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        return GradeResult(False, 2, 6, f"Init container present but pod {name} not Ready (Phase: {phase})")
    restarts = ctx.get_pod_restart_count(pod)
    if restarts > 2:
        return GradeResult(False, 5, 6, f"Pod {name} Ready but {restarts} restarts indicate residual permission failures on /data/db")
    return GradeResult(True, 6, 6, f"Pod {name} is 1/1 Running with initContainer correcting subPath ownership")
