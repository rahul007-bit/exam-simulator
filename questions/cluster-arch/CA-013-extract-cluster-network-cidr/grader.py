from core.graderlib import KubernetesContext, GradeResult
import ipaddress
import json
import re
import os

FILE = "/tmp/cluster-network.json"
CIDR_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$")

def find_cidr(entries, keyword):
    for key, value in entries.items():
        if keyword in key.lower() and isinstance(value, str) and CIDR_RE.match(value.strip()):
            return value.strip()
    return None

def grade(ctx: KubernetesContext) -> GradeResult:
    if not ctx.is_reachable():
        return GradeResult(False, 0, 3, "Cluster unreachable via context k3d-cka", skipped=True)
    if not os.path.isfile(FILE):
        return GradeResult(False, 0, 3, f"Output file {FILE} does not exist on this host")
    try:
        with open(FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        return GradeResult(False, 0, 3, f"{FILE} is not valid JSON: {e}")
    if not isinstance(data, dict) or not data:
        return GradeResult(False, 1, 3, f"{FILE} is valid JSON but not a non-empty object with CIDR fields")
    score = 1
    pod_cidr = find_cidr(data, "pod")
    svc_cidr = find_cidr(data, "service")
    if not pod_cidr:
        return GradeResult(False, 1, 3, f"No valid pod CIDR found in {FILE} (keys: {list(data)})")
    score = 2
    if not svc_cidr:
        return GradeResult(False, 2, 3, f"Pod CIDR {pod_cidr} recorded but no valid service CIDR found in {FILE}")

    node_cidrs = {n.get("spec", {}).get("podCIDR") for n in ctx.get_nodes()} - {None}
    matched_pod = False
    try:
        cand_net = ipaddress.ip_network(pod_cidr)
        for nc in node_cidrs:
            nc_net = ipaddress.ip_network(nc)
            if cand_net == nc_net or nc_net.subnet_of(cand_net) or cand_net.subnet_of(nc_net):
                matched_pod = True
                break
    except ValueError:
        return GradeResult(False, 1, 3, f"Invalid pod CIDR format: {pod_cidr}")

    if node_cidrs and not matched_pod:
        return GradeResult(False, 2, 3, f"Pod CIDR {pod_cidr} does not match cluster pod network ({sorted(node_cidrs)})")

    svc_ip = (ctx.kubectl(["get", "svc", "kubernetes"]) or {}).get("spec", {}).get("clusterIP")
    if svc_ip:
        try:
            if ipaddress.ip_address(svc_ip) not in ipaddress.ip_network(svc_cidr):
                return GradeResult(False, 2, 3, f"Service CIDR {svc_cidr} does not contain kubernetes service IP {svc_ip}")
        except ValueError:
            return GradeResult(False, 2, 3, f"Invalid service CIDR {svc_cidr} in {FILE}")

    return GradeResult(True, 3, 3, f"Cluster network CIDRs verified: podCIDR={pod_cidr}, serviceCIDR={svc_cidr}")
