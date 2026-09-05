from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    pc_high = ctx.get_resource("priorityclass", "high-priority")
    pc_low = ctx.get_resource("priorityclass", "low-priority")
    if not pc_high or pc_high.get("value") != 1000000:
        val = pc_high.get("value") if pc_high else None
        return GradeResult(False, 0, 6, f"PriorityClass high-priority missing or value={val}, expected 1000000")
    if not pc_low or pc_low.get("value") != 1000:
        val = pc_low.get("value") if pc_low else None
        return GradeResult(False, 1, 6, f"PriorityClass low-priority missing or value={val}, expected 1000")
    pods = ctx.get_pods("task-scheduler")
    high = [p for p in pods if p.get("spec", {}).get("priorityClassName") == "high-priority"]
    if not high:
        return GradeResult(False, 2, 6, "No pod with priorityClassName high-priority found in task-scheduler")
    hp = high[0]
    if hp.get("status", {}).get("phase") != "Running":
        return GradeResult(False, 3, 6, f"High-priority pod {hp['metadata']['name']} is {hp.get('status', {}).get('phase')}, expected Running")
    if not ctx.check_pod_ready(hp):
        return GradeResult(False, 4, 6, f"High-priority pod {hp['metadata']['name']} is not Ready (expected 1/1)")
    low = [p for p in pods if p.get("spec", {}).get("priorityClassName") == "low-priority"]
    events = ctx.kubectl(["get", "events"], namespace="task-scheduler") or {}
    preempt_events = [i for i in events.get("items", []) if "preempt" in (i.get("reason", "") + " " + i.get("message", "")).lower()]
    if not low and not preempt_events:
        return GradeResult(False, 5, 6, "No low-priority victim pods or preemption events found in task-scheduler")
    preempted = [p["metadata"]["name"] for p in low if p.get("status", {}).get("phase") != "Running" or p.get("status", {}).get("reason") == "Evicted"]
    if not preempted and not preempt_events:
        return GradeResult(False, 5, 6, "All low-priority pods are still Running; no evidence of preemption")
    return GradeResult(True, 6, 6, f"High-priority pod {hp['metadata']['name']} runs 1/1 after preempting low-priority pods")
