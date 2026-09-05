from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    netpol = k8s.get_networkpolicy("gateway-mesh", "protect-order-svc")
    if not netpol:
        return False, 0, 4, "NetworkPolicy protect-order-svc not found"

    pod_sel = netpol.get("spec", {}).get("podSelector", {}).get("matchLabels", {})
    if pod_sel.get("app") != "order-svc":
        return False, 1, 4, f"Pod selector is {pod_sel}, expected app: order-svc"

    ingress_rules = netpol.get("spec", {}).get("ingress", [])
    if not ingress_rules:
        return False, 2, 4, "No ingress rules specified in NetworkPolicy"

    return True, 4, 4, "NetworkPolicy properly restricts traffic to order-svc pods"
