from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)

    node = ctx.get_resource("node", "k3d-dev-agent-0")
    if not node:
        # Fallback to get_nodes
        nodes = ctx.get_nodes()
        node = next((n for n in nodes if n.get("metadata", {}).get("name") == "k3d-dev-agent-0"), None)

    if not node:
        return GradeResult(False, 0, 3, "Worker node k3d-dev-agent-0 not found in cluster")

    # Verify node is cordoned/drained
    if not node.get("spec", {}).get("unschedulable"):
        return GradeResult(False, 0, 3, "Node k3d-dev-agent-0 is still schedulable (node has not been drained)")

    # Verify no active non-daemonset pods are running on k3d-dev-agent-0
    pods = ctx.get_pods(namespace="maintenance-ops")
    agent_pods = [
        p for p in pods
        if p.get("spec", {}).get("nodeName") == "k3d-dev-agent-0"
        and p.get("status", {}).get("phase") == "Running"
    ]
    if agent_pods:
        names = [p.get("metadata", {}).get("name") for p in agent_pods]
        return GradeResult(False, 1, 3, f"Node is cordoned but pods are still running on k3d-dev-agent-0: {names}")

    return GradeResult(True, 3, 3, "Worker node k3d-dev-agent-0 safely drained and workloads evicted")
