from core.graderlib import KubernetesContext, GradeResult
import re
from datetime import datetime, timezone

PKI = "/etc/kubernetes/pki"
MIN_DAYS = 360

def cert_days_left(ctx: KubernetesContext, path: str):
    out = ctx.ssh_cmd("NODE_1", f"openssl x509 -enddate -noout -in {path} 2>/dev/null")
    if not out:
        return None
    m = re.search(r"notAfter=(.+)", out)
    if not m:
        return None
    try:
        expiry = datetime.strptime(m.group(1).strip(), "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return (expiry - datetime.now(timezone.utc)).days

def grade(ctx: KubernetesContext) -> GradeResult:
    if ctx.ssh_cmd("NODE_1", "echo up") != "up":
        return GradeResult(False, 0, 3, "kubeadm node NODE_1 unreachable via SSH", skipped=True)
    if ctx.ssh_cmd("NODE_1", "true") is None:
        return GradeResult(False, 0, 3, "kubeadm node unreachable via SSH", skipped=True)
    apiserver_days = cert_days_left(ctx, f"{PKI}/apiserver.crt")
    if apiserver_days is None:
        return GradeResult(False, 0, 3, f"Could not read expiry of {PKI}/apiserver.crt on control-plane node")
    if apiserver_days < MIN_DAYS:
        return GradeResult(False, 0, 3, f"apiserver.crt expires in {apiserver_days} days (< {MIN_DAYS}); certificates were not renewed")
    return GradeResult(True, 3, 3, f"Control plane certificates renewed: apiserver.crt has {apiserver_days}d remaining validity")

