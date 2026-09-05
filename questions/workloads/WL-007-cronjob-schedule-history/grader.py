from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    cj = ctx.get_resource("cronjob", "log-cleaner", "batch-schedules")
    if not cj:
        return GradeResult(False, 0, 2, "CronJob log-cleaner not found in batch-schedules")
    sched = cj.get("spec", {}).get("schedule")
    limit = cj.get("spec", {}).get("successfulJobsHistoryLimit")
    if sched != "*/15 * * * *" or limit != 3:
        return GradeResult(False, 1, 2, f"CronJob spec wrong: schedule={sched!r} (expected '*/15 * * * *'), successfulJobsHistoryLimit={limit} (expected 3)")
    return GradeResult(True, 2, 2, "CronJob log-cleaner runs */15 * * * * with successfulJobsHistoryLimit 3")
