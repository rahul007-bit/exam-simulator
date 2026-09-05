from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    job = ctx.get_resource("job", "batch-sync", "data-import")
    if not job:
        return GradeResult(False, 0, 3, "Job batch-sync not found in data-import")
    limit = job.get("spec", {}).get("backoffLimit")
    if limit is None or limit < 10:
        return GradeResult(False, 0, 3, f"backoffLimit is {limit}, expected 10")
    succeeded = int(job.get("status", {}).get("succeeded", 0) or 0)
    if succeeded < 1:
        failed = int(job.get("status", {}).get("failed", 0) or 0)
        return GradeResult(False, 0, 3, f"Job not complete (succeeded={succeeded}, failed={failed}); fix the command typo and recreate so it completes")
    return GradeResult(True, 3, 3, "batch-sync completed successfully (1/1) with backoffLimit 10")
