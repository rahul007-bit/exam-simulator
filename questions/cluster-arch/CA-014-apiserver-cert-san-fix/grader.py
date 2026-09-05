from core.graderlib import KubernetesContext, GradeResult

LB_IP = "10.0.0.50"
APISERVER_CRT = "/etc/kubernetes/pki/apiserver.crt"

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 4, "kubeadm node NODE_1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", "true") is None:
        return GradeResult(False, 0, 4, "kubeadm node unreachable via SSH", skipped=True)
    score = 0
    msgs = []
    san = ctx.ssh_cmd("NODE_1", f"openssl x509 -text -noout -in {APISERVER_CRT} 2>/dev/null | grep -c '{LB_IP}'")
    if san and san.strip() != "0":
        score += 2
        msgs.append(f"apiserver.crt contains SAN {LB_IP}")
    else:
        msgs.append(f"apiserver.crt does not contain IP SAN {LB_IP} (cert not regenerated)")
    cfg = ctx.ssh_cmd(
        "NODE_1",
        f"grep -ls '{LB_IP}' /etc/kubernetes/kubeadm-config.yaml /etc/kubernetes/kubeadm.yaml 2>/dev/null | head -1",
    )
    if cfg:
        score += 1
        msgs.append(f"kubeadm config {cfg.strip()} lists {LB_IP} in certSANs")
    else:
        msgs.append(f"no kubeadm config under /etc/kubernetes lists {LB_IP}")
    ready = ctx.ssh_cmd("NODE_1", "kubectl --kubeconfig=/etc/kubernetes/admin.conf get --raw /readyz 2>/dev/null")
    if ready and "ok" in ready.lower():
        score += 1
        msgs.append("API server readyz ok")
    else:
        msgs.append("API server not healthy via admin.conf")
    return GradeResult(score == 4, score, 4, "; ".join(msgs))
