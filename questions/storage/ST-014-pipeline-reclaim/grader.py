from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pvc = k8s.get_pvc("storage-pipeline", "pipeline-pvc")
    if pvc:
        return False, 0, 3, "PVC pipeline-pvc still exists, must be deleted"

    pv = k8s.get_pv("pipeline-pv")
    if not pv:
        return False, 0, 3, "PV pipeline-pv was deleted, expected Released status"

    phase = pv.get("status", {}).get("phase")
    if phase != "Released":
        return False, 1, 3, f"PV phase is {phase}, expected Released"

    return True, 3, 3, "PV successfully retained in Released state after claim deletion"
