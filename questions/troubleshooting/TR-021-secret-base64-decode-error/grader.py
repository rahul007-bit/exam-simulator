from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    secret = ctx.get_secret("payments", "api-keys")
    if not secret:
        return GradeResult(False, 0, 2, "Secret api-keys not found in payments")
    sec_data = secret.get("data", {}) or {}
    if "DB_PASS" not in sec_data:
        return GradeResult(False, 0, 2, "Key DB_PASS not found in secret api-keys")
    pod = ctx.get_pod("payments", "crypto-service")
    if not pod:
        return GradeResult(False, 0, 2, "Pod crypto-service not found in payments")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        return GradeResult(False, 1, 2, f"Secret api-keys DB_PASS configured but pod crypto-service is not Ready (Phase: {phase})")
    return GradeResult(True, 2, 2, "Secret api-keys has DB_PASS and pod crypto-service is 1/1 Running")
