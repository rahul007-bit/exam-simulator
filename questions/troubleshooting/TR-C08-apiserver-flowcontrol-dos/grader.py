from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    fs_data = ctx.kubectl(["get", "flowschemas"])
    items = fs_data.get("items", []) if isinstance(fs_data, dict) else []
    if not items:
        return GradeResult(False, 0, 6, "No FlowSchemas returned (flowcontrol API unreachable or defaults removed)")
    by_name = {i.get("metadata", {}).get("name"): i for i in items}
    exempt = by_name.get("exempt")
    if not exempt or exempt.get("spec", {}).get("prioritizationLevel") != "exempt":
        return GradeResult(False, 0, 6, "Exempt FlowSchema missing or no longer prioritizationLevel exempt (restore defaults)")
    target = by_name.get("catch-all-exempt") or by_name.get("catch-all")
    if not target:
        return GradeResult(False, 2, 6, "Catch-all FlowSchema missing; delete the modified FlowSchema so the API server recreates the default")
    spec = target.get("spec", {})
    if spec.get("prioritizationLevel") != "exempt":
        limited = spec.get("limited") or {}
        if int(limited.get("nominalConcurrencyShares", 20) or 0) <= 0:
            return GradeResult(False, 2, 6, f"FlowSchema {target.get('metadata', {}).get('name')} still has 0 concurrency seats (nominalConcurrencyShares)")
    dns = ctx.get_pods("kube-system", label_selector="k8s-app=kube-dns")
    if not dns or not all(ctx.check_pod_ready(p) for p in dns):
        return GradeResult(False, 4, 6, "FlowSchema restored but background controllers still not reconciling (CoreDNS not Ready)")
    return GradeResult(True, 6, 6, "FlowSchema defaults restored and control-plane controllers reconciling (CoreDNS Ready)")
