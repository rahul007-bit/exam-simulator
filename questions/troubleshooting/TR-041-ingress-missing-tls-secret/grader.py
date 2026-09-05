from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    ing = ctx.get_ingress("tls-ingress", "secure-web")
    if not ing:
        return GradeResult(False, 0, 3, "Ingress secure-web not found in tls-ingress")
    tls = ing.get("spec", {}).get("tls") or []
    if "web-tls-cert" not in [t.get("secretName") for t in tls]:
        return GradeResult(False, 0, 3, "Ingress secure-web spec.tls does not reference secret web-tls-cert")
    sec = ctx.get_secret("tls-ingress", "web-tls-cert")
    if not sec:
        return GradeResult(False, 0, 3, "Secret web-tls-cert does not exist in tls-ingress")
    if sec.get("type") != "kubernetes.io/tls":
        return GradeResult(False, 0, 3, f"Secret web-tls-cert has type {sec.get('type')!r}, expected kubernetes.io/tls")
    data = sec.get("data", {})
    if not data.get("tls.crt") or not data.get("tls.key"):
        return GradeResult(False, 0, 3, "Secret web-tls-cert is missing tls.crt or tls.key data")
    return GradeResult(True, 3, 3, "Ingress secure-web uses valid TLS secret web-tls-cert")
