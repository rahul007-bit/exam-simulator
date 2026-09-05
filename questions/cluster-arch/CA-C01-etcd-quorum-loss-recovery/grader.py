from core.graderlib import KubernetesContext, GradeResult
import json

ETCDCTL = (
    "etcdctl --endpoints=https://127.0.0.1:2379 "
    "--cacert=/etc/kubernetes/pki/etcd/ca.crt "
    "--cert=/etc/kubernetes/pki/etcd/server.crt "
    "--key=/etc/kubernetes/pki/etcd/server.key"
)

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 6, "kubeadm node NODE_1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", "true") is None:
        return GradeResult(False, 0, 6, "kubeadm node unreachable via SSH", skipped=True)
    score = 0
    msgs = []
    health = ctx.ssh_cmd("NODE_1", f"{ETCDCTL} endpoint health 2>/dev/null")
    if health and "is healthy" in health:
        score += 2
        msgs.append("etcd endpoint healthy")
    else:
        msgs.append("etcd endpoint not healthy (etcdctl endpoint health failed)")
    members_out = ctx.ssh_cmd("NODE_1", f"{ETCDCTL} member list -w json 2>/dev/null")
    try:
        members = json.loads(members_out).get("members", []) if members_out else None
    except json.JSONDecodeError:
        members = None
    if members is not None and len(members) == 1:
        score += 2
        msgs.append(f"single-member cluster ({members[0].get('name', 'unknown')})")
    elif members is not None:
        msgs.append(f"cluster has {len(members)} members, expected exactly 1 after --force-new-cluster bootstrap")
    else:
        msgs.append("could not list etcd members")
    pod = ctx.ssh_cmd(
        "NODE_1",
        "kubectl get pods -n kube-system --kubeconfig=/etc/kubernetes/admin.conf 2>/dev/null | grep etcd- | grep -c Running",
    )
    if pod and pod.strip() != "0":
        score += 1
        msgs.append("etcd static pod Running")
    else:
        msgs.append("etcd static pod not Running")
    ready = ctx.ssh_cmd("NODE_1", "kubectl --kubeconfig=/etc/kubernetes/admin.conf get --raw /readyz 2>/dev/null")
    if ready and "ok" in ready.lower():
        score += 1
        msgs.append("API server readyz ok")
    else:
        msgs.append("API server not healthy")
    return GradeResult(score == 6, score, 6, "; ".join(msgs))
