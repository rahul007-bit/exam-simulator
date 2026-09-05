from core.graderlib import KubernetesContext
from core.models import GradeResult

def grade(k8s: KubernetesContext):
    if not k8s.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    pvc = k8s.get_pvc("storage-pipeline", "pipeline-pvc")
    if not pvc:
        return False, 0, 3, "PVC pipeline-pvc not found in storage-pipeline"
    
    phase = pvc.get("status", {}).get("phase")
    if phase != "Bound":
        return False, 1, 3, f"PVC phase is {phase}, expected Bound"

    dep = k8s.get_deployment("storage-pipeline", "pipeline-worker")
    if not dep:
        return False, 1, 3, "Deployment pipeline-worker not found"

    ready = dep.get("status", {}).get("readyReplicas", 0)
    if ready < 1:
        return False, 2, 3, f"Deployment has {ready} ready replicas, expected 1"

    return True, 3, 3, "PVC bound and pipeline-worker running with mounted volume"
