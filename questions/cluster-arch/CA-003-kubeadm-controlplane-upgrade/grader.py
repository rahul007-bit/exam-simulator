from core.graderlib import KubernetesContext, GradeResult

TARGET = "v1.30"

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 4, "kubeadm node NODE_1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", "true") is None:
        return GradeResult(False, 0, 4, "kubeadm node unreachable via SSH", skipped=True)
    score = 0
    msgs = []
    kubeadm_ver = ctx.ssh_cmd("NODE_1", "kubeadm version -o short 2>/dev/null")
    if kubeadm_ver and kubeadm_ver.strip().startswith(TARGET):
        score += 1
        msgs.append(f"kubeadm at {kubeadm_ver.strip()}")
    else:
        msgs.append(f"kubeadm binary not {TARGET}.x (got {kubeadm_ver or 'unavailable'})")
    kubelet_ver = ctx.ssh_cmd("NODE_1", "kubelet --version 2>/dev/null")
    kubelet_ok = bool(kubelet_ver) and kubelet_ver.strip().split()[-1].startswith(TARGET)
    if kubelet_ok:
        score += 1
        msgs.append(f"kubelet at {kubelet_ver.strip().split()[-1]}")
    else:
        msgs.append(f"kubelet binary not {TARGET}.x (got {kubelet_ver or 'unavailable'})")
    node_ver = ctx.ssh_cmd(
        "NODE_1",
        "kubectl get node $(hostname) --kubeconfig=/etc/kubernetes/admin.conf -o jsonpath='{.status.nodeInfo.kubeletVersion}' 2>/dev/null",
    )
    if node_ver and node_ver.strip().startswith(TARGET):
        score += 2
        msgs.append(f"registered node reports kubeletVersion {node_ver.strip()}")
    else:
        msgs.append(f"node kubeletVersion via admin.conf not {TARGET}.x (got {node_ver or 'query failed'})")
    return GradeResult(score == 4, score, 4, "; ".join(msgs))
