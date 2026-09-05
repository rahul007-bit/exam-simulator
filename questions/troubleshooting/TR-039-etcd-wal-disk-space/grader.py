from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 4, "kubeadm node unreachable via SSH", skipped=True)
    valid = ctx.ssh_cmd("NODE_1", "python3 -c \"import yaml;yaml.safe_load(open('/etc/kubernetes/manifests/etcd.yaml'))\" && echo valid")
    if valid != "valid":
        return GradeResult(False, 0, 4, "Etcd static pod manifest /etc/kubernetes/manifests/etcd.yaml missing or unparseable on NODE_1")
    active = ctx.ssh_cmd("NODE_1", "systemctl is-active kubelet")
    if active != "active":
        return GradeResult(False, 2, 4, "etcd.yaml is valid but kubelet is not active on NODE_1")
    running = ctx.ssh_cmd("NODE_1", "crictl ps -q --name etcd")
    if not running:
        return GradeResult(False, 3, 4, "Kubelet active but etcd container is not running (WAL lock on /var/lib/etcd not cleared)")
    if ctx.is_reachable():
        etcd_pods = [p for p in ctx.get_pods("kube-system") if str(p.get("metadata", {}).get("name", "")).startswith("etcd-")]
        if etcd_pods and not all(ctx.check_pod_ready(p) for p in etcd_pods):
            return GradeResult(False, 3, 4, "Etcd container running but etcd pod is not Ready in kube-system")
    return GradeResult(True, 4, 4, "Etcd manifest valid, kubelet active and etcd member running healthy")
