"""
Offline unit verification for the dynamic Incus provisioning engine.
Runs IncusClusterManager against a stateful fake `incus` binary.

Covers:
  U1. Graceful fallback when Incus CLI is unavailable.
  U2. Dynamic remote discovery (filters builtins/public/non-incus/unresponsive).
  U3. Dynamic role distribution (round-robin across remotes, local fallback).
  U4. Fast CoW snapshot launch (<=20s) with security.nesting + resource caps.
  U5. Full cluster provisioning (parallel launch, bootstrap, join).
  U6. Node readiness polling + kubeconfig retrieval.
  U7. Idempotent teardown (double delete leaves zero instances).
"""
import os
import sys
import json
import time
import tempfile
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

TMP = Path(tempfile.mkdtemp(prefix="fake-incus-"))
STATE_FILE = TMP / "state.json"
FAKE = TMP / "fake_incus.py"

FAKE.write_text((Path(__file__).resolve().parent / "fake_incus.py").read_text(encoding="utf-8"), encoding="utf-8")
if os.name == "nt":
    SHIM = TMP / "incus.cmd"
    SHIM.write_text(f'@echo off\r\npython "{FAKE}" %*\r\n', encoding="utf-8")
else:
    SHIM = TMP / "incus"
    SHIM.write_text(f'#!/bin/sh\nexec python3 "{FAKE}" "$@"\n', encoding="utf-8")
    SHIM.chmod(0o755)


def base_state():
    return {
        "remotes": {
            "nodeA": {"Public": False, "Protocol": "incus", "_responsive": True, "Addr": "10.0.0.10:8443"},
            "nodeB": {"Public": False, "Protocol": "incus", "_responsive": False, "Addr": "10.0.0.11:8443"},
            "images": {"Public": True, "Protocol": "simplestreams", "Addr": "https://images.example"},
        },
        "instances": {},
        "nodes_ready": True,
        "pools": [{"name": "default", "driver": "zfs"}],
        "volumes": [],
    }


def reset_state():
    STATE_FILE.write_text(json.dumps(base_state()), encoding="utf-8")


def make_manager(env_bin=None):
    import importlib
    os.environ["FAKE_INCUS_STATE"] = str(STATE_FILE)
    if env_bin is None:
        os.environ["INCUS_BIN"] = str(SHIM)
    else:
        os.environ["INCUS_BIN"] = env_bin
    import core.incus_manager as im
    importlib.reload(im)
    return im.IncusClusterManager(), im


PASS = []
FAIL = []


def check(name, cond, detail=""):
    if cond:
        PASS.append(name)
        print(f"  PASS  {name}")
    else:
        FAIL.append(name)
        print(f"  FAIL  {name}  {detail}")


print("== U1: Unavailable Incus -> graceful fallback ==")
mgr, im = make_manager(env_bin="definitely-not-incus-xyz")
check("U1 is_available False", mgr.is_available() is False)
check("U1 discover empty", mgr.discover_compute_remotes() == [])
try:
    mgr.delete_session_cluster("session-test01")
    check("U1 teardown no-crash", True)
except Exception as e:
    check("U1 teardown no-crash", False, str(e))

print("== U2: Dynamic remote discovery ==")
reset_state()
mgr, im = make_manager()
remotes = mgr.discover_compute_remotes()
check("U2 only healthy compute remotes", remotes == ["nodeA"], f"got {remotes}")
check("U2 has_remote nodeA", mgr.has_remote("nodeA") is True)
check("U2 has_remote nodeB (unresponsive)", mgr.has_remote("nodeB") is False)
check("U2 has_remote local", mgr.has_remote("local") is True)

print("== U3: Dynamic role distribution ==")
dist = mgr.get_target_distribution(["node1", "node2", "node3"], is_distributed=True)
check("U3 control plane local, workers on nodeA",
      dist == {"node1": None, "node2": "nodeA", "node3": "nodeA"}, str(dist))
dist_local = mgr.get_target_distribution(["node1", "node2"], is_distributed=False)
check("U3 is_distributed=False -> local", all(v is None for v in dist_local.values()), str(dist_local))

print("== U4: Fast CoW snapshot launch ==")
reset_state()
mgr, im = make_manager()
# seed a snapshot source instance
STATE_FILE.write_text(json.dumps({**base_state(), "instances": {"nodeA:k8s-golden-snap": {"status": "Running", "config": {}, "ip": "10.10.0.50"}}}), encoding="utf-8")
t0 = time.time()
ok = mgr.launch_node("node1-utest", remote_name="nodeA", snapshot="k8s-golden-snap", cpu_limit="2", mem_limit="2GiB")
elapsed = time.time() - t0
check("U4 CoW launch ok", ok is True)
check("U4 <= 20s", elapsed <= 20, f"{elapsed:.2f}s")
state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
inst = state["instances"].get("nodeA:node1-utest", {})
cfg = inst.get("config", {})
check("U4 instance Running", inst.get("status") == "Running", str(state["instances"].keys()))
check("U4 security.nesting=true", cfg.get("security.nesting") == "true", str(cfg))
check("U4 cpu cap", cfg.get("limits.cpu") == "2", str(cfg))
check("U4 mem cap", cfg.get("limits.memory") == "2GiB", str(cfg))
ip = mgr.get_node_ip("node1-utest", remote_name="nodeA")
check("U4 get_node_ip", ip == "10.10.0.50", str(ip))

print("== U4b: Golden snapshot bootstrap + fast snapshot-copy launch ==")
reset_state()
mgr, im = make_manager()
src = mgr.ensure_golden_snapshot(remote_name="nodeA")
check("U4b golden snapshot src", src == "nodeA:golden-k8s/gold", str(src))
state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
check("U4b golden instance created", "nodeA:golden-k8s" in state["instances"], str(list(state["instances"])))
check("U4b snapshot registered", "gold" in state.get("snapshots", {}).get("nodeA:golden-k8s", []), str(state.get("snapshots")))
src2 = mgr.ensure_golden_snapshot(remote_name="nodeA")
check("U4b idempotent (no re-bootstrap)", src2 == src, str(src2))
# Full provisioning must now take the fast snapshot-copy path
ips = mgr.provision_kubeadm_cluster("session-utest", is_distributed=True)
state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
sess = sorted(k for k in state["instances"] if "utest" in k)
check("U4b 3 nodes via snapshot copy", len(sess) == 3, str(sess))
check("U4b golden preserved after provision", "nodeA:golden-k8s" in state["instances"])
mgr.delete_session_cluster("session-utest")
state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
check("U4b teardown spares golden", "nodeA:golden-k8s" in state["instances"], str(list(state["instances"])))

print("== U5: Full cluster provisioning (3 nodes) ==")
reset_state()
mgr, im = make_manager()
ips = mgr.provision_kubeadm_cluster("session-utest", is_distributed=True)
check("U5 three node IPs", sorted(ips.keys()) == ["node1", "node2", "node3"] and all(ips.values()), str(ips))
state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
names = sorted(k for k in state["instances"] if "utest" in k)
check("U5 3 instances created", len(names) == 3, str(names))
check("U5 control plane local, workers on nodeA",
      set(names) == {"node1-session-utest", "nodeA:node2-session-utest", "nodeA:node3-session-utest"}, str(names))

print("== U6: Readiness + kubeconfig ==")
ready = mgr.wait_for_nodes_ready("session-utest", expected_count=3, timeout=15, interval=1)
check("U6 all nodes Ready", ready is True)
status = mgr.check_nodes_ready("session-utest", expected_count=3)
check("U6 ready_count == 3", status.get("ready_count") == 3, str(status))
kubecfg = mgr.get_kubeconfig("session-utest", remotes_map={"node1": "nodeA"})
check("U6 kubeconfig retrieved", kubecfg is not None and "kind: Config" in kubecfg, repr(kubecfg)[:80])
check("U6 kubeconfig via discovery fallback", mgr.get_kubeconfig("session-utest") is not None)

print("== U7: Idempotent teardown ==")
mgr.delete_session_cluster("session-utest")
state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
remaining = [k for k in state["instances"] if "utest" in k]
check("U7 first teardown purges all", remaining == [], str(remaining))
try:
    mgr.delete_session_cluster("session-utest")  # second call: nothing left
    check("U7 second teardown no-op", True)
except Exception as e:
    check("U7 second teardown no-op", False, str(e))
state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
remaining = [k for k in state["instances"] if "utest" in k]
check("U7 zero orphans", remaining == [], str(remaining))

print()
print(f"RESULT: {len(PASS)} passed, {len(FAIL)} failed")
sys.exit(1 if FAIL else 0)
