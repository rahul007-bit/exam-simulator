from core.graderlib import KubernetesContext, GradeResult

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 4, "kubeadm node unreachable via SSH", skipped=True)
    present = ctx.ssh_cmd("NODE_1", "test -f /etc/kubernetes/manifests/kube-apiserver.yaml && echo present")
    if present != "present":
        return GradeResult(False, 0, 4, "Static pod manifest /etc/kubernetes/manifests/kube-apiserver.yaml missing on NODE_1")
    valid = ctx.ssh_cmd("NODE_1", "python3 -c \"import yaml;yaml.safe_load(open('/etc/kubernetes/manifests/kube-apiserver.yaml'))\" && echo valid")
    if valid != "valid":
        return GradeResult(False, 0, 4, "kube-apiserver.yaml does not parse as valid YAML (flag typo still present)")
    running = ctx.ssh_cmd("NODE_1", "crictl ps -q --name kube-apiserver")
    if not running:
        return GradeResult(False, 2, 4, "Manifest is valid YAML but kube-apiserver container is not running (invalid flag not corrected)")
    return GradeResult(True, 4, 4, "kube-apiserver static pod manifest is valid and the apiserver container is running")
