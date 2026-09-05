from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    cj = ctx.get_resource("cronjob", "daily-report", "batch-schedules")
    if not cj:
        return GradeResult(False, 0, 3, "CronJob daily-report not found in batch-schedules")
    policy = cj.get("spec", {}).get("concurrencyPolicy")
    jobs = ctx.list_resources("job", "batch-schedules")
    owned = [j for j in jobs if any(o.get("kind") == "CronJob" and o.get("name") == "daily-report" for o in j.get("metadata", {}).get("ownerReferences", []) or [])]
    active = [j["metadata"]["name"] for j in owned if (j.get("status", {}).get("active") or 0) > 0]
    if policy != "Replace":
        if active:
            return GradeResult(False, 0, 3, f"concurrencyPolicy is {policy} and hung job(s) still active: {', '.join(active)}")
        return GradeResult(False, 1, 3, f"Stuck job cleared but concurrencyPolicy is {policy}, expected Replace")
    return GradeResult(True, 3, 3, "concurrencyPolicy is Replace; daily-report can start new jobs")
