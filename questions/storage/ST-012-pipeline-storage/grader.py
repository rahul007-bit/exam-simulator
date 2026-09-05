from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    sc = k8s.get_storageclass("pipeline-sc")
    if not sc:
        return False, 0, 3, "StorageClass pipeline-sc not found"
    
    if sc.get("reclaimPolicy") != "Retain":
        return False, 1, 3, f"StorageClass reclaimPolicy is {sc.get('reclaimPolicy')}, expected Retain"

    pv = k8s.get_pv("pipeline-pv")
    if not pv:
        return False, 1, 3, "PersistentVolume pipeline-pv not found"
    
    cap = pv.get("spec", {}).get("capacity", {}).get("storage")
    if cap != "5Gi":
        return False, 2, 3, f"PV capacity is {cap}, expected 5Gi"

    return True, 3, 3, "StorageClass and PersistentVolume configured correctly"
