from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 2, "Cluster unreachable via context k3d-cka", skipped=True)
    pv = ctx.get_pv("local-node-pv")
    if not pv:
        return GradeResult(False, 0, 2, "PersistentVolume local-node-pv not found")
    spec = pv.get("spec", {})
    cap = spec.get("capacity", {}).get("storage")
    modes = spec.get("accessModes", [])
    ok_base = cap == "5Gi" and "ReadWriteOnce" in modes and spec.get("storageClassName") == "local-disk" and spec.get("hostPath", {}).get("path") == "/opt/data"
    if not ok_base:
        return GradeResult(False, 1, 2, f"PV local-node-pv invalid: capacity={cap}, accessModes={modes}, storageClassName={spec.get('storageClassName')}, hostPath={spec.get('hostPath', {}).get('path')}")
    terms = spec.get("nodeAffinity", {}).get("required", {}).get("nodeSelectorTerms", [])
    match = any(any(e.get("key") == "kubernetes.io/hostname" and e.get("operator") == "In" and "k3d-cka-server-0" in e.get("values", []) for e in t.get("matchExpressions", [])) for t in terms)
    if not match:
        return GradeResult(False, 1, 2, "PV local-node-pv nodeAffinity does not target node k3d-cka-server-0")
    return GradeResult(True, 2, 2, "PV local-node-pv created with correct spec and nodeAffinity for k3d-cka-server-0")
