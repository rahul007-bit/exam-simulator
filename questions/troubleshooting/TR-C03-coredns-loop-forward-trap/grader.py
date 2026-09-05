from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)
    cm = ctx.get_configmap("kube-system", "coredns")
    if not cm:
        return GradeResult(False, 0, 6, "ConfigMap kube-system/coredns not found")
    corefile = cm.get("data", {}).get("Corefile", "")
    svc = ctx.get_service("kube-system", "kube-dns")
    dns_ip = (svc or {}).get("spec", {}).get("clusterIP", "")
    if "forward . /etc/resolv.conf" not in corefile:
        return GradeResult(False, 0, 6, "Corefile does not restore 'forward . /etc/resolv.conf' (circular forward still in place)")
    if dns_ip and dns_ip in corefile:
        return GradeResult(False, 0, 6, f"Corefile still forwards to kube-dns ClusterIP {dns_ip} (self-referential loop remains)")
    dep = ctx.get_deployment("kube-system", "coredns")
    pods = ctx.get_pods("kube-system", label_selector="k8s-app=kube-dns")
    ready = [p for p in pods if ctx.check_pod_ready(p)]
    if not ready or (dep and ctx.deployment_ready_replicas(dep) < 1):
        return GradeResult(False, 3, 6, "Corefile fixed but CoreDNS pods are not Ready yet (delete pods to clear the crashloop)")
    restarts = sum(ctx.get_pod_restart_count(p) for p in pods)
    if restarts > 2:
        return GradeResult(False, 5, 6, f"CoreDNS Ready but {restarts} total restarts show residual loop crashloops; delete pods for a clean state")
    return GradeResult(True, 6, 6, "Corefile forwards to /etc/resolv.conf, loop broken and CoreDNS pods stable and Ready")
