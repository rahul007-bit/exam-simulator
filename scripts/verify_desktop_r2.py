import sys, time, subprocess

sys.path.insert(0, "/root/cka-labs")
from core.incus_manager import incus_mgr
from core.desktop_manager import desktop_mgr

SESSION = "verify-r2"
PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}", flush=True)

def dex(args, timeout=30):
    return subprocess.run(["docker", "exec", "-u", "exam", f"cka-desktop-{SESSION}"] + args,
                          capture_output=True, text=True, timeout=timeout)

print(f"=== R2 Desktop Kubeconfig Verification (session={SESSION}) ===", flush=True)

print("step 1: provisioning kubeadm cluster...", flush=True)
t0 = time.time()
ips = incus_mgr.provision_kubeadm_cluster(SESSION, is_distributed=True)
check("cluster provisioned", len(ips) == 3, str(ips))
print(f"  info  {time.time()-t0:.0f}s", flush=True)

ready = incus_mgr.wait_for_nodes_ready(SESSION, expected_count=3, timeout=120, interval=5)
check("3 nodes Ready", ready)

print("step 2: starting candidate desktop (kubeconfig injection via Redis)...", flush=True)
ok = desktop_mgr.start_desktop(SESSION, redis_host="172.17.0.1")
check("desktop container started", ok)

time.sleep(3)

print("step 3: verifying kubeadm-vms context inside container...", flush=True)
r = dex(["kubectl", "config", "get-contexts"])
check("kubeadm-vms context exists in container", "kubeadm-vms" in r.stdout, r.stdout.replace("\n", " | ")[:200])

r = dex(["kubectl", "--context", "kubeadm-vms", "get", "nodes", "--no-headers"])
ready_count = r.stdout.count("Ready")
check("kubectl --context=kubeadm-vms sees 3 Ready nodes", ready_count >= 3,
      (r.stdout or r.stderr).replace("\n", " | ")[:220])

check("verify_container_kubeconfig() helper", desktop_mgr.verify_container_kubeconfig(SESSION))

r = dex(["kubectl", "get", "pods", "-A", "--context", "kubeadm-vms", "--no-headers"])
print(f"  info  control-plane pods: {len(r.stdout.splitlines())}", flush=True)

print("step 4: cleanup...", flush=True)
desktop_mgr.stop_desktop(SESSION)
incus_mgr.delete_session_cluster(SESSION)
check("desktop container removed", not desktop_mgr.is_desktop_running(SESSION))

print(f"\n=== R2 RESULT: {len(PASS)} passed, {len(FAIL)} failed ===", flush=True)
sys.exit(1 if FAIL else 0)
