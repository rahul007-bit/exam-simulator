from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    pvcs = ctx.list_resources("pvc", "local-storage")
    if not pvcs:
        return GradeResult(False, 0, 6, "No PVC found in local-storage")
    pvc = pvcs[0]
    score = 1
    pods = ctx.get_pods("local-storage")
    if not pods:
        return GradeResult(False, score, 6, f"PVC {pvc['metadata']['name']} exists but no pod was found in local-storage")
    score = 2
    phase = pvc.get("status", {}).get("phase")
    if phase != "Bound":
        return GradeResult(False, score, 6, f"PVC {pvc['metadata']['name']} phase is {phase}, expected Bound")
    score = 4
    pod = pods[0]
    if pod.get("status", {}).get("phase") != "Running":
        return GradeResult(False, score, 6, f"PVC is Bound but pod {pod['metadata']['name']} is {pod.get('status', {}).get('phase')}")
    score = 5
    if not ctx.check_pod_ready(pod):
        return GradeResult(False, score, 6, f"Pod {pod['metadata']['name']} is Running but not Ready")
    pv = ctx.get_pv(pvc.get("spec", {}).get("volumeName"))
    terms = pv.get("spec", {}).get("nodeAffinity", {}).get("required", {}).get("nodeSelectorTerms", []) if pv else []
    allowed = [v for t in terms for e in t.get("matchExpressions", []) if e.get("key") == "kubernetes.io/hostname" for v in e.get("values", [])]
    node = pod.get("spec", {}).get("nodeName")
    if allowed and node not in allowed:
        return GradeResult(False, 5, 6, f"Pod runs on node {node} but PV nodeAffinity only allows {allowed}")
    return GradeResult(True, 6, 6, f"PVC {pvc['metadata']['name']} is Bound and pod {pod['metadata']['name']} is Running on intended node {node}")
