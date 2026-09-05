from core.graderlib import KubernetesContext, GradeResult

RESTORED = "/var/lib/etcd-restored"
MANIFEST = "/etc/kubernetes/manifests/etcd.yaml"

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 4, "kubeadm node NODE_1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", "true") is None:
        return GradeResult(False, 0, 4, "kubeadm node unreachable via SSH", skipped=True)
    score = 0
    if ctx.ssh_cmd("NODE_1", f"test -d {RESTORED}") is None:
        return GradeResult(False, 0, 4, f"Restored data directory {RESTORED} does not exist on control-plane node")
    if ctx.ssh_cmd("NODE_1", f"test -d {RESTORED}/member") is None:
        data_msg = f"{RESTORED} exists but has no member/ data (snapshot restore output missing)"
    else:
        score = 2
        data_msg = f"Restored etcd data present in {RESTORED}/member"
    manifest_ref = ctx.ssh_cmd("NODE_1", f"grep -c '{RESTORED}' {MANIFEST}")
    if manifest_ref:
        score += 2
        data_msg += f"; {MANIFEST} references {RESTORED}"
    else:
        data_msg += f"; {MANIFEST} does not reference {RESTORED}"
    return GradeResult(score == 4, score, 4, data_msg)
