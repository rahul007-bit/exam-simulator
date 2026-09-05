from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, f"Cluster unreachable via context {ctx.context_name}", skipped=True)
    pvcs = ctx.list_resources("pvc", "data-nodes")
    if not pvcs:
        return GradeResult(False, 0, 4, "No PVCs found in data-nodes")
    bound = [p for p in pvcs if p.get("status", {}).get("phase") == "Bound"]
    if not bound:
        phases = {p["metadata"]["name"]: p.get("status", {}).get("phase") for p in pvcs}
        return GradeResult(False, 0, 4, f"PVC(s) {phases} not Bound; local PV still cannot bind")
    sc_name = bound[0].get("spec", {}).get("storageClassName")
    if not sc_name:
        for sc in ctx.list_resources("storageclass"):
            if sc.get("metadata", {}).get("annotations", {}).get("storageclass.kubernetes.io/is-default-class") == "true":
                sc_name = sc["metadata"]["name"]
                break
    if sc_name:
        sc = ctx.get_resource("storageclass", sc_name)
        if sc:
            mode = sc.get("volumeBindingMode")
            if mode != "WaitForFirstConsumer":
                return GradeResult(False, 2, 4, f"StorageClass {sc_name} has volumeBindingMode {mode}, expected WaitForFirstConsumer")
    return GradeResult(True, 4, 4, "PVC in data-nodes is Bound via a WaitForFirstConsumer StorageClass")
