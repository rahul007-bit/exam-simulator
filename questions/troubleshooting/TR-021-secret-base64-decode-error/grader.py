import base64

from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    secret = ctx.get_secret("payments", "api-keys")
    if not secret:
        return GradeResult(False, 0, 2, "Secret api-keys not found in payments")
    bad = []
    for key, val in secret.get("data", {}).items():
        try:
            base64.b64decode(val, validate=True)
        except Exception:
            bad.append(key)
    if bad:
        return GradeResult(False, 0, 2, "Secret api-keys still contains corrupted base64 in key(s): " + ", ".join(bad))
    pod = ctx.get_pod("payments", "crypto-service")
    if not pod:
        return GradeResult(False, 0, 2, "Pod crypto-service not found in payments")
    if not ctx.check_pod_ready(pod):
        phase = pod.get("status", {}).get("phase")
        return GradeResult(False, 1, 2, f"Secret api-keys data is valid but pod crypto-service is not Ready (Phase: {phase})")
    return GradeResult(True, 2, 2, "Secret api-keys decodes cleanly and pod crypto-service is 1/1 Running")
