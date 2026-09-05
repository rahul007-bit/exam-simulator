from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    role = k8s.get_role("secure-pipeline", "config-manager")
    if not role:
        return False, 0, 4, "Role config-manager not found"

    rules = role.get("rules", [])
    has_res_names = False
    for r in rules:
        res_names = r.get("resourceNames", [])
        if "app-config" in res_names or "app-secret" in res_names:
            has_res_names = True
            break

    if not has_res_names:
        return False, 2, 4, "Role config-manager does not restrict via resourceNames"

    return True, 4, 4, "RBAC tightened with exact resourceNames constraints"
