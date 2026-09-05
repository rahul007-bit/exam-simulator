from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    job = ctx.get_resource("job", "batch-processor", "batch-processing")
    if not job:
        return GradeResult(False, 0, 2, "Job batch-processor not found in batch-processing")
    spec = job.get("spec", {})
    comps, par, back = spec.get("completions"), spec.get("parallelism"), spec.get("backoffLimit")
    if (comps, par, back) != (5, 2, 4):
        return GradeResult(False, 1, 2, f"Job spec wrong: completions={comps} (expected 5), parallelism={par} (expected 2), backoffLimit={back} (expected 4)")
    succeeded = job.get("status", {}).get("succeeded", 0)
    if succeeded < 1:
        return GradeResult(True, 2, 2, "Job batch-processor spec correct (no succeeded pods yet, completion not required)")
    return GradeResult(True, 2, 2, f"Job batch-processor spec correct with {succeeded}/5 completions succeeded")
