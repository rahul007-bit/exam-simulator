from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(passed=False, score=0, max_score=4, message="Cluster unreachable via context k3d-cka", skipped=True)

    ns = ctx.get_resource("namespace", "secure-zone")
    if not ns:
        return GradeResult(False, 0, 4, "Namespace secure-zone not found")

    labels = ns.get("metadata", {}).get("labels", {}) or {}
    mode = labels.get("pod-security.kubernetes.io/enforce")
    if not mode:
        return GradeResult(False, 0, 4, f"Namespace secure-zone has no pod-security.kubernetes.io/enforce label (labels: {labels})")
    if mode != "restricted":
        return GradeResult(False, 2, 4, f"Namespace secure-zone PSS enforce label is {mode}, expected restricted")

    return GradeResult(True, 4, 4, "Namespace secure-zone enforces Pod Security Standard restricted via pod-security.kubernetes.io/enforce label")
