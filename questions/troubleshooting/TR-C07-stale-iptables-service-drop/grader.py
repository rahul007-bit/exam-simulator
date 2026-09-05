from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 6, "Cluster unreachable via context k3d-cka", skipped=True)

    eps = ctx.get_endpoints("default", "kubernetes")
    if not eps or not eps.get("subsets"):
        return GradeResult(False, 0, 6, "kubernetes service has no endpoints (service dataplane control broken)")

    # Live connectivity probe: resolve an in-cluster name against the kube-dns
    # ClusterIP from inside a running pod. With the rogue drop rule in place
    # this times out; after it is removed it succeeds.
    dns_svc = ctx.get_service("kube-system", "kube-dns")
    dns_ip = (dns_svc or {}).get("spec", {}).get("clusterIP")
    probe_pod = None
    for p in ctx.get_pods("kube-system"):
        name = (p.get("metadata") or {}).get("name") or ""
        if "local-path-provisioner" in name and ctx.check_pod_ready(p):
            probe_pod = name
            break

    if probe_pod and dns_ip:
        out = ctx.kubectl(
            ["exec", "-n", "kube-system", probe_pod, "--",
             "nslookup", "kubernetes.default.svc.cluster.local", dns_ip],
            as_json=False, timeout=20,
        )
        if out is None or "Address" not in (out or ""):
            return GradeResult(False, 2, 6,
                f"In-cluster service connectivity still broken: DNS query to ClusterIP {dns_ip} from pod {probe_pod} failed (rogue drop rule likely persists)")

    proxy_pods = ctx.get_pods("kube-system", label_selector="k8s-app=kube-proxy")
    ready_proxy = [p for p in proxy_pods if ctx.check_pod_ready(p)]
    if proxy_pods and len(ready_proxy) < len(proxy_pods):
        return GradeResult(False, 2, 6, f"kube-proxy pods not healthy: {len(ready_proxy)}/{len(proxy_pods)} Ready (restart them after clearing the drop rule)")

    cm = ctx.get_configmap("kube-system", "kube-proxy")
    if cm and "apiVersion" not in cm.get("data", {}).get("config.conf", ""):
        return GradeResult(False, 2, 6, "kube-proxy config.conf is not a valid KubeProxyConfiguration")

    nodes = ctx.get_nodes()
    not_ready = [
        n.get("metadata", {}).get("name") for n in nodes
        if not any(c.get("type") == "Ready" and c.get("status") == "True" for c in n.get("status", {}).get("conditions", []))
    ]
    if not_ready:
        return GradeResult(False, 4, 6, f"Nodes not Ready: {', '.join(not_ready)} (stale iptables drop rule likely persists on that node)")

    dns = ctx.get_pods("kube-system", label_selector="k8s-app=kube-dns")
    if not dns or not all(ctx.check_pod_ready(p) for p in dns):
        return GradeResult(False, 4, 6, "CoreDNS pods not Ready; in-cluster service traffic still impaired")

    return GradeResult(True, 6, 6, "Service connectivity restored: in-cluster DNS via ClusterIP works, nodes Ready, kube-proxy and CoreDNS healthy")
