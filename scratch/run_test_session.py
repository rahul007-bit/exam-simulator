import os, sys, time, argparse

sys.path.insert(0, "/root/cka-labs")
os.chdir("/root/cka-labs")
os.environ.setdefault("REDIS_HOST", "127.0.0.1")
os.environ.setdefault("ENABLE_EPHEMERAL_K3D", "1")
os.environ.setdefault("ENABLE_MICROVMS", "1")
os.environ.setdefault("SINGLE_NODE", "0")

from core.loader import QuestionLoader
from core.models import ExamSession
from core.deployer import LabDeployer
from core.grader import LabGrader
from core.incus_manager import incus_mgr
from core.k3d_manager import k3d_mgr
from core.desktop_manager import desktop_mgr
from core.sandbox_orchestrator import orchestrator

KUBEADM_IDS = ["CA-001", "CA-011", "CA-012", "TR-033", "TR-018"]
K3D_IDS = ["SC-001", "SC-005", "CA-009", "WL-001", "TR-003"]
ORDER = ["SC-001", "SC-005", "CA-009", "WL-001", "TR-003",
         "TR-018", "TR-033", "CA-012", "CA-001", "CA-011"]

PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", default=None)
    args = ap.parse_args()
    sid = args.session or f"session-{int(time.time())}"

    print(f"=== 10-Question Mixed Test Session (k3d x5 + kubeadm x5) session={sid} ===", flush=True)

    # 1. Kubeadm fleet (synchronous so we know the node IPs for NODE_* env)
    print("[1/5] provisioning kubeadm fleet...", flush=True)
    t0 = time.time()
    ips = incus_mgr.provision_kubeadm_cluster(sid, is_distributed=True)
    check("fleet provisioned (3 nodes)", len(ips) == 3, str(ips))
    print(f"  info  {time.time()-t0:.0f}s", flush=True)
    ready = incus_mgr.wait_for_nodes_ready(sid, expected_count=3, timeout=240, interval=5)
    check("kubeadm nodes Ready", ready)
    for role, ip in ips.items():
        os.environ[f"NODE_{role[-1]}"] = ip
    print(f"  info  NODE env: NODE_1={os.environ.get('NODE_1')} NODE_2={os.environ.get('NODE_2')} NODE_3={os.environ.get('NODE_3')}", flush=True)

    # 2. Ephemeral k3d cluster
    print("[2/5] creating ephemeral k3d cluster...", flush=True)
    k3d_ok = k3d_mgr.create_ephemeral_cluster(sid, redis_host="172.17.0.1")
    check("k3d cluster ready", k3d_ok)

    # 3. Desktop container (injects merged kubeconfig: k3d-cka + kubeadm-vms)
    print("[3/5] starting candidate desktop...", flush=True)
    desk_ok = desktop_mgr.start_desktop(sid, redis_host="172.17.0.1")
    check("desktop started", desk_ok)
    time.sleep(2)

    r = subprocess_run(["kubectl", "config", "get-contexts", "-o", "name"])
    check("host kubeconfig has k3d-cka", "k3d-cka" in (r or ""))
    check("host kubeconfig has kubeadm-vms", "kubeadm-vms" in (r or ""))

    # 4. Select + deploy the 10 questions (sequential steps set per-task context)
    print("[4/5] deploying 10 tasks...", flush=True)
    loader = QuestionLoader()
    deployer = LabDeployer()
    picked = [loader._registry[qid] for qid in ORDER if qid in loader._registry]
    missing = [qid for qid in ORDER if qid not in loader._registry]
    if missing:
        check("all questions found", False, f"missing {missing}")
    k3d_sel = [q for q in picked if q.target_context == "k3d-cka"]
    kub_sel = [q for q in picked if q.target_context == "kubeadm-vms"]
    check("5 k3d questions", len(k3d_sel) == 5, [q.id for q in k3d_sel])
    check("5 kubeadm questions", len(kub_sel) == 5, [q.id for q in kub_sel])

    deployer.clear_session()
    deployer._cleanup_cluster_resources(picked)
    session = ExamSession(
        session_id=sid,
        created_at=time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
        name="Mixed Test (5 k3d + 5 kubeadm)",
        questions=picked,
        target_contexts=sorted({q.target_context for q in picked}),
        time_limit_minutes=60,
        mode="sequential",
        current_index=0,
        scores={},
    )
    deployer.save_session(session)
    deploy_ok = 0
    for idx in range(len(picked)):
        try:
            if deployer.deploy_step(session, idx):
                deploy_ok += 1
        except Exception as ex:
            print(f"  deploy_step {idx} error: {ex}", flush=True)
    check("10 task setups executed", deploy_ok == 10, f"{deploy_ok}/10 steps ok")

    # 5. Grade (nothing solved -> expect FAIL/0 per task, proves graders run live)
    print("[5/5] grading...", flush=True)
    grader = LabGrader()
    summaries = grader.grade_session(session)
    grader.render_scorecard(summaries)
    scored = sum(s.result.score for s in summaries)
    maxed = sum(s.result.max_score for s in summaries)
    errored = [f"{s.question.id}: {s.result.message}" for s in summaries if "error" in s.result.message.lower()]
    check("graders executed cleanly (no infra errors)", not errored, str(errored)[:300])
    check("not-attempted score is 0", scored == 0, f"{scored}/{maxed}")

    # 6. Teardown everything
    print("[6/6] teardown...", flush=True)
    orchestrator.teardown_session(sid)
    time.sleep(2)
    check("desktop removed", not desktop_mgr.is_desktop_running(sid))
    left = [i["name"] for i in incus_mgr.list_all_fleet_instances() if sid.replace("session-", "") in i.get("name", "") or sid in i.get("name", "")]
    check("zero orphan incus instances", left == [], str(left))

    print(f"\n=== SESSION RESULT: {len(PASS)} passed, {len(FAIL)} failed ===", flush=True)
    return 1 if FAIL else 0

def subprocess_run(args):
    import subprocess
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=10)
        return r.stdout or ""
    except Exception:
        return ""

if __name__ == "__main__":
    sys.exit(main())
