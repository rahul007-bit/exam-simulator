from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    target = None
    for p in ctx.get_pods("log-collector"):
        if "logger" in [c.get("name") for c in p.get("spec", {}).get("containers", [])]:
            target = p
            break
    if not target:
        return GradeResult(False, 0, 4, "No pod running container 'logger' found in log-collector")
    name = target.get("metadata", {}).get("name")
    inits = target.get("spec", {}).get("initContainers", [])
    if not inits:
        return GradeResult(False, 0, 4, f"Pod {name} has no initContainer creating /var/log/app on the shared volume")
    if not ctx.check_pod_ready(target):
        phase = target.get("status", {}).get("phase")
        return GradeResult(False, 2, 4, f"Init container present but pod {name} not Ready (Phase: {phase})")
    if ctx.get_pod_restart_count(target) > 5:
        return GradeResult(False, 3, 4, f"Pod {name} Ready but has excessive restarts (logger still racing on /var/log/app)")
    return GradeResult(True, 4, 4, "Init container prepares /var/log/app and both app and logger containers are Ready (2/2)")
