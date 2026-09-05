from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    sec = k8s.get_secret("gateway-mesh", "gateway-tls-secret")
    if not sec:
        return False, 0, 3, "TLS Secret gateway-tls-secret not found"

    ing = k8s.get_ingress("gateway-mesh", "mesh-gateway")
    if not ing:
        return False, 1, 3, "Ingress mesh-gateway not found"

    rules = ing.get("spec", {}).get("rules", [])
    if not rules:
        return False, 1, 3, "No ingress rules defined"

    paths = [p.get("path") for p in rules[0].get("http", {}).get("paths", [])]
    if "/auth" not in paths or "/orders" not in paths:
        return False, 2, 3, f"Ingress paths {paths} missing /auth or /orders"

    tls = ing.get("spec", {}).get("tls", [])
    if not tls:
        return False, 2, 3, "Ingress lacks TLS configuration"

    return True, 3, 3, "Multi-path TLS Ingress gateway configured correctly"
