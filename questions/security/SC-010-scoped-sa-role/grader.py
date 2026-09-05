from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    sa = k8s.get_serviceaccount("secure-pipeline", "pipeline-runner")
    if not sa:
        return False, 0, 2, "ServiceAccount pipeline-runner not found"

    role = k8s.get_role("secure-pipeline", "config-manager")
    if not role:
        return False, 1, 2, "Role config-manager not found"

    rb = k8s.get_rolebinding("secure-pipeline", "pipeline-config-binding")
    if not rb:
        return False, 1, 2, "RoleBinding pipeline-config-binding not found"

    return True, 2, 2, "ServiceAccount and scoped RoleBinding configured correctly"
