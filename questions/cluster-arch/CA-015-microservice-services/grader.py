from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    auth_svc = k8s.get_service("gateway-mesh", "auth-svc")
    if not auth_svc:
        return False, 0, 2, "Service auth-svc not found"
    
    order_svc = k8s.get_service("gateway-mesh", "order-svc")
    if not order_svc:
        return False, 1, 2, "Service order-svc not found"

    auth_ep = k8s.get_endpoints("gateway-mesh", "auth-svc")
    order_ep = k8s.get_endpoints("gateway-mesh", "order-svc")

    if not auth_ep or not order_ep:
        return False, 1, 2, "One or more services lack active backend endpoints"

    return True, 2, 2, "Microservice backends and clusterIP services operational"
