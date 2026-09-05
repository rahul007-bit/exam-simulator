from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    wh = ctx.kubectl(["get", "mutatingwebhookconfigurations", "admission-hook"])
    if not wh or "webhooks" not in wh:
        return GradeResult(False, 0, 4, "MutatingWebhookConfiguration admission-hook not found")
    webhooks = wh.get("webhooks", [])
    if not webhooks:
        return GradeResult(False, 0, 4, "MutatingWebhookConfiguration admission-hook defines no webhooks")
    failing = [w.get("name") for w in webhooks if w.get("failurePolicy", "Fail") == "Fail"]
    if failing:
        if len(failing) < len(webhooks):
            return GradeResult(False, 2, 4, "failurePolicy still Fail for webhook(s): " + ", ".join(failing))
        return GradeResult(False, 0, 4, "failurePolicy is still Fail on admission-hook; pods cannot schedule while the webhook is down")
    return GradeResult(True, 4, 4, "admission-hook failurePolicy is Ignore; pods can schedule in policy-enforcement")
