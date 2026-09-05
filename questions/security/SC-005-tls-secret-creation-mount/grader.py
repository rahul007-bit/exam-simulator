from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(passed=False, score=0, max_score=2, message="Cluster unreachable via context k3d-cka", skipped=True)

    secret = ctx.get_secret("secure-ingress", "app-tls-secret")
    if not secret:
        return GradeResult(False, 0, 2, "Secret app-tls-secret not found in secure-ingress")
    if secret.get("type") != "kubernetes.io/tls":
        return GradeResult(False, 0, 2, f"Secret app-tls-secret has type {secret.get('type')}, expected kubernetes.io/tls")
    if "tls.crt" not in secret.get("data", {}) or "tls.key" not in secret.get("data", {}):
        return GradeResult(False, 0, 2, "Secret app-tls-secret is missing tls.crt or tls.key data entries")

    pod = ctx.get_pod("secure-ingress", "tls-web")
    if not pod:
        return GradeResult(False, 1, 2, "TLS secret app-tls-secret is valid but pod tls-web not found in secure-ingress")

    volumes = {v.get("name"): v for v in pod.get("spec", {}).get("volumes", [])}
    for c in pod.get("spec", {}).get("containers", []):
        for vm in c.get("volumeMounts", []):
            v = volumes.get(vm.get("name"), {})
            path = vm.get("mountPath", "")
            if v.get("secret", {}).get("secretName") == "app-tls-secret" and path in ("/etc/tls", "/etc/tls/"):
                if ctx.check_pod_ready(pod):
                    return GradeResult(True, 2, 2, "Pod tls-web mounts TLS secret app-tls-secret at /etc/tls and is Running")
                return GradeResult(True, 2, 2, "Pod tls-web mounts TLS secret app-tls-secret at /etc/tls (pod not Running yet)")

    return GradeResult(False, 1, 2, "Pod tls-web does not mount secret app-tls-secret at /etc/tls")
