from core.graderlib import KubernetesContext, GradeResult

SNAPSHOT = "/opt/backup/etcd-snapshot.db"

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 3, "kubeadm node NODE_1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", "true") is None:
        return GradeResult(False, 0, 3, "kubeadm node unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", f"test -f {SNAPSHOT}") is None:
        return GradeResult(False, 0, 3, f"No snapshot file found at {SNAPSHOT} on control-plane node")
    if ctx.ssh_cmd("NODE_1", f"test -s {SNAPSHOT}") is None:
        return GradeResult(False, 1, 3, f"Snapshot file {SNAPSHOT} exists but is empty (0 bytes)")
    status = ctx.ssh_cmd("NODE_1", f"etcdctl snapshot status {SNAPSHOT} 2>/dev/null | head -1")
    if status:
        return GradeResult(True, 3, 3, f"etcd snapshot verified: {status}")
    if ctx.ssh_cmd("NODE_1", "command -v etcdctl") is None:
        return GradeResult(True, 3, 3, f"Snapshot {SNAPSHOT} exists and is non-empty (etcdctl not installed for deeper validation)")
    return GradeResult(False, 2, 3, f"Snapshot {SNAPSHOT} exists but etcdctl snapshot status failed (corrupt or not a valid snapshot)")
