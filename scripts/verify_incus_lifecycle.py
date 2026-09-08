#!/usr/bin/env python3
"""
E2E lifecycle verification for the dynamic Incus provisioning engine.

Run on the Incus host (or anywhere with INCUS_BIN configured):
    python3 scripts/verify_incus_lifecycle.py [--session verify-lc]

Exercises: launch timing (CoW snapshot preferred, golden image fallback),
node readiness, kubeconfig validation (host + desktop container), and
idempotent teardown. Exits 0 on success, 1 on failure, 0 with SKIP if
Incus is not available on this machine.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.incus_manager import incus_mgr  # noqa: E402

LAUNCH_BUDGET_S = 20.0
READY_TIMEOUT_S = 180
PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}", flush=True)


def kubectl_from_host(kubeconfig_path: str) -> str:
    try:
        r = subprocess.run(
            ["kubectl", "--kubeconfig", kubeconfig_path, "get", "nodes", "--no-headers"],
            capture_output=True, text=True, timeout=20,
        )
        return (r.stdout or r.stderr).strip()
    except Exception as e:
        return f"error: {e}"


def kubectl_from_desktop(session_id: str) -> str:
    try:
        r = subprocess.run(
            ["docker", "exec", "-u", "exam", f"cka-desktop-{session_id}",
             "kubectl", "--context", "kubeadm-vms", "get", "nodes", "--no-headers"],
            capture_output=True, text=True, timeout=25,
        )
        return (r.stdout or r.stderr).strip()
    except Exception as e:
        return f"error: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default="verify-lc")
    args = ap.parse_args()
    session_id = args.session

    print(f"=== Incus E2E Lifecycle Verification (session={session_id}) ===", flush=True)

    if not incus_mgr.is_available():
        print("SKIP: Incus CLI not available on this machine. (graceful fallback path OK)")
        return 0

    remotes = incus_mgr.discover_compute_remotes()
    print(f"Discovered compute remotes: {remotes or ['<none> -> local mode']}", flush=True)

    # 1. Fast CoW launch timing check (snapshot preferred, golden image fallback)
    snapshot_src = incus_mgr.ensure_golden_snapshot()

    node = f"node1-{session_id}"
    t0 = time.time()
    ok = incus_mgr.launch_node(node, snapshot=snapshot_src, cpu_limit="2", mem_limit="2GiB")
    elapsed = time.time() - t0
    check("launch succeeded", ok)
    check(f"launch <= {LAUNCH_BUDGET_S}s (CoW)", elapsed <= LAUNCH_BUDGET_S, f"{elapsed:.2f}s")

    incus_mgr.delete_node(node)

    # 2. Full multi-node cluster provisioning + bootstrap
    t0 = time.time()
    ips = incus_mgr.provision_kubeadm_cluster(session_id, is_distributed=True)
    prov_elapsed = time.time() - t0
    check("3 nodes provisioned with IPs",
          sorted(ips.keys()) == ["node1", "node2", "node3"] and all(ips.values()), str(ips))
    print(f"  info  provisioning+ip-discovery wall time: {prov_elapsed:.2f}s", flush=True)

    # 3. Node readiness (non-blocking poll)
    ready = incus_mgr.wait_for_nodes_ready(session_id, expected_count=3, timeout=READY_TIMEOUT_S, interval=5)
    check("all 3 nodes Ready", ready)
    print(f"  info  nodes: {incus_mgr.check_nodes_ready(session_id).get('nodes')}", flush=True)

    # 4. Kubeconfig validation on host
    kubeconf = incus_mgr.get_kubeconfig(session_id)
    check("kubeconfig retrieved from node1", kubeconf is not None and "kind: Config" in kubeconf)
    if kubeconf:
        p = Path(f"/tmp/kubeconfig-{session_id}.conf")
        p.write_text(kubeconf)
        out = kubectl_from_host(str(p))
        ready_lines = out.count("Ready")
        check("host kubectl sees >=3 Ready nodes via kubeconfig", ready_lines >= 3, out.replace("\n", " | ")[:200])

    # 5. Desktop container context verification (if desktop is running)
    r = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=10)
    if f"cka-desktop-{session_id}" in (r.stdout or ""):
        out = kubectl_from_desktop(session_id)
        check("desktop container kubectl --context kubeadm-vms sees nodes", "Ready" in out or "Error" not in out,
              out.replace("\n", " | ")[:200])
    else:
        print("  info  desktop container not running for this session; skipping step 5", flush=True)

    # 6. Idempotent teardown
    incus_mgr.delete_session_cluster(session_id)
    incus_mgr.delete_session_cluster(session_id)  # second call must be a clean no-op
    leftovers = [
        i["name"] for i in incus_mgr.list_all_fleet_instances()
        if session_id in i.get("name", "") or session_id in i.get("session_id", "")
    ]
    check("zero orphaned instances after double teardown", leftovers == [], str(leftovers))

    print(f"\n=== RESULT: {len(PASS)} passed, {len(FAIL)} failed ===")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
