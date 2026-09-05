from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 4, "Cluster unreachable via context k3d-cka", skipped=True)
    dep = ctx.get_deployment("multi-zone-app", "zone-spread")
    if not dep:
        return GradeResult(False, 0, 4, "Deployment zone-spread not found in multi-zone-app")
    tscs = dep.get("spec", {}).get("template", {}).get("spec", {}).get("topologySpreadConstraints", [])
    tsc = next((t for t in tscs if t.get("maxSkew") == 1 and t.get("topologyKey") == "topology.kubernetes.io/zone" and t.get("whenUnsatisfiable") == "DoNotSchedule"), None)
    if not tsc:
        return GradeResult(False, 0, 4, f"topologySpreadConstraints wrong: {tscs} (need maxSkew 1, topology.kubernetes.io/zone, DoNotSchedule)")
    spec = dep.get("spec", {})
    if spec.get("replicas", 0) < 2 or dep.get("status", {}).get("readyReplicas", 0) != spec.get("replicas"):
        return GradeResult(False, 2, 4, f"Deployment zone-spread has {dep.get('status', {}).get('readyReplicas')}/{spec.get('replicas')} ready replicas")
    sel = ",".join(f"{k}={v}" for k, v in spec.get("selector", {}).get("matchLabels", {}).items())
    pods = [p for p in ctx.get_pods("multi-zone-app", sel) if p.get("status", {}).get("phase") == "Running" and p.get("spec", {}).get("nodeName")]
    zones = {n["metadata"]["name"]: n.get("metadata", {}).get("labels", {}).get("topology.kubernetes.io/zone") for n in ctx.get_nodes()}
    counts = {}
    for p in pods:
        z = zones.get(p["spec"]["nodeName"])
        if z:
            counts[z] = counts.get(z, 0) + 1
    if len(counts) >= 2 and max(counts.values()) - min(counts.values()) > 1:
        return GradeResult(False, 3, 4, f"Pods spread across zones {counts} violates maxSkew 1")
    return GradeResult(True, 4, 4, f"Deployment zone-spread spreads pods across zones with maxSkew 1: {counts}")
