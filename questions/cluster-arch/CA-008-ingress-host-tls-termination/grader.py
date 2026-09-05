from core.graderlib import KubernetesContext, GradeResult

NS = "tls-routing"

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    ing = ctx.get_ingress(NS, "secure-app")
    if not ing:
        return GradeResult(False, 0, 3, f"Ingress secure-app not found in {NS}")
    score = 1
    rules = ing.get("spec", {}).get("rules", [])
    hosts = [r.get("host") for r in rules]
    if "app.company.org" not in hosts:
        return GradeResult(False, 1, 3, f"Ingress host is {hosts or 'unset'}, expected app.company.org")
    score = 2
    tls = ing.get("spec", {}).get("tls", [])
    tls_ok = any(
        t.get("secretName") == "app-cert" and (not t.get("hosts") or "app.company.org" in t.get("hosts", []))
        for t in tls
    )
    if not tls_ok:
        return GradeResult(False, 2, 3, "spec.tls does not reference secret app-cert for app.company.org")
    backends = {
        (p.get("backend", {}).get("service", {}).get("name"), p.get("backend", {}).get("service", {}).get("port", {}).get("number"))
        for r in rules if r.get("host") == "app.company.org"
        for p in r.get("http", {}).get("paths", [])
    }
    if ("app-svc", 80) not in backends:
        return GradeResult(False, 2, 3, f"Host app.company.org routes to {backends or 'nothing'}, expected app-svc:80")
    return GradeResult(True, 3, 3, "Ingress secure-app terminates TLS for app.company.org via app-cert and routes to app-svc:80")
