from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(passed=False, score=0, max_score=4, message="Cluster unreachable via context k3d-cka", skipped=True)

    pod = ctx.get_pod("auth-tokens", "vault-agent")
    if not pod:
        return GradeResult(False, 0, 4, "Pod vault-agent not found in auth-tokens")

    proj = None
    for v in pod.get("spec", {}).get("volumes", []):
        if v.get("name") == "vault-token" and v.get("projected"):
            for src in v["projected"].get("sources", []):
                if "serviceAccountToken" in src:
                    proj = src["serviceAccountToken"]
                    break
    if not proj:
        vols = [(v.get("name"), "projected" if v.get("projected") else "other") for v in pod.get("spec", {}).get("volumes", [])]
        return GradeResult(False, 0, 4, f"Pod vault-agent has no projected volume named vault-token with a serviceAccountToken source (volumes: {vols})")

    audience = proj.get("audience")
    expiry = proj.get("expirationSeconds")
    if audience != "vault.company.io" or expiry != 3600:
        return GradeResult(False, 2, 4, f"Token projection configured but audience={audience} (want vault.company.io), expirationSeconds={expiry} (want 3600)")

    if ctx.check_pod_ready(pod):
        return GradeResult(True, 4, 4, "Pod vault-agent projects a serviceAccountToken with audience vault.company.io and expirationSeconds 3600 and is Running")
    return GradeResult(True, 4, 4, "Pod vault-agent projects a serviceAccountToken with audience vault.company.io and expirationSeconds 3600 (pod not Running yet)")
