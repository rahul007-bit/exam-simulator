"""
API-driven platform verification v2: CANDIDATE persona + ADMIN persona, HTTP only.
Run on the mgmt node against the live web server (port 3000).

Personas:
  CANDIDATE: admin issues invite -> candidate starts with token -> navigates,
             flags, uses clipboard -> submits. Events must be actor=candidate.
  ADMIN:     login/check/infrastructure/terminate. Events must be actor=admin.

Regression: after submit/terminate, polling GET /api/session must NOT
resurrect desktop containers (AutoRestore bug fix).
"""
import json, os, sys, time, urllib.request, urllib.error, subprocess

BASE = "http://127.0.0.1:3000"
RECORDINGS_DIR = "/root/cka-labs/recordings"
QUESTION_IDS = ["SC-001", "SC-005", "CA-009", "WL-001", "TR-003",
                "TR-018", "TR-033", "CA-012", "CA-001", "CA-011"]
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

PASS, FAIL = [], []

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {str(detail)[:200]}", flush=True)

def api(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}

def incus_names_all():
    names = []
    for scope in ("", "node1:", "node2:", "node3:"):
        r = subprocess.run(["incus", "list", scope, "--format", "json"], capture_output=True, text=True, timeout=25)
        try:
            names += [i.get("name", "") for i in json.loads(r.stdout or "[]")]
        except Exception:
            pass
    return names

def docker_names():
    r = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True, timeout=10)
    return [n.strip() for n in r.stdout.splitlines() if n.strip()]

def k3d_clusters():
    r = subprocess.run(["k3d", "cluster", "list"], capture_output=True, text=True, timeout=10)
    return r.stdout or ""

def events_of(sid):
    p = os.path.join(RECORDINGS_DIR, f"{sid}.events.jsonl")
    if not os.path.exists(p):
        return []
    return [json.loads(l) for l in open(p) if l.strip()]

def wait_fleet(sid, timeout=420):
    t0 = time.time()
    while time.time() - t0 < timeout:
        names = incus_names_all()
        hits = [n for n in names if sid in n and n.startswith(("node1-", "node2-", "node3-"))]
        if len(hits) >= 3:
            return True, time.time() - t0
        time.sleep(5)
    return False, time.time() - t0

def main():
    print("=== API Platform Verification v2 (candidate + admin) ===", flush=True)

    # ---------- ADMIN: login ----------
    st, login = api("POST", "/api/admin/login", {"password": ADMIN_PASSWORD})
    check("A1 admin login", st == 200 and bool(login.get("token")))
    ah = {"Authorization": f"Bearer {login.get('token', '')}"}
    st, chk = api("GET", "/api/admin/check", headers=ah)
    check("A2 admin check", st == 200 and chk.get("authenticated") is True)
    st, _ = api("GET", "/api/admin/infrastructure")
    check("A3 infrastructure requires auth (401 anon)", st == 401)

    # ---------- CANDIDATE: invite -> start ----------
    print("C1: admin issues invite; candidate starts via token...", flush=True)
    st, inv = api("POST", "/api/admin/sessions/create", {}, headers=ah)
    check("C1 invite created", st == 200 and bool(inv.get("token")), str(inv)[:100])
    invite_token = inv.get("token", "")

    st, resp = api("POST", "/api/start", {"question_ids": QUESTION_IDS, "candidate_token": invite_token})
    check("C1 candidate start 200", st == 200, f"{st} {str(resp)[:120]}")
    sid = resp.get("session_id")
    cand_tok = resp.get("candidate_token")
    check("C1 session bound to invite token", cand_tok == invite_token, f"{cand_tok} vs {invite_token}")
    check("C1 total_tasks == 10", resp.get("total_tasks") == 10, resp.get("total_tasks"))
    check("C1 current task is first k3d (SC-001)", (resp.get("current_task") or {}).get("id") == "SC-001",
          (resp.get("current_task") or {}).get("id"))
    print(f"  info  session={sid} candidate_token={cand_tok[:8]}...", flush=True)

    # ---------- CANDIDATE: navigation ----------
    print("C2: candidate navigation...", flush=True)
    st, r = api("POST", "/api/action/jump", {"task_num": 3})
    check("C2 jump task 3 (CA-009)", st == 200 and (r.get("current_task") or {}).get("id") == "CA-009", (r.get("current_task") or {}).get("id"))
    st, r = api("POST", "/api/action/flag", {"task_num": 3})
    check("C2 flag task 3", st == 200 and r.get("is_flagged") is True)
    st, r = api("POST", "/api/clipboard", {"action": "copy", "text": "kubectl get nodes"})
    check("C2 clipboard copy", st == 200)
    st, r = api("POST", "/api/action/retry")
    check("C2 retry current task", st == 200)
    st, r = api("POST", "/api/action/jump", {"task_num": 7})
    check("C2 jump to kubeadm task 7 (TR-033)", st == 200 and (r.get("current_task") or {}).get("id") == "TR-033")

    ok, dt = wait_fleet(sid)
    check("C2 fleet 3 nodes Running", ok, f"{dt:.0f}s")

    # ---------- CANDIDATE: submit ----------
    print("C3: candidate submits...", flush=True)
    st, report = api("POST", "/api/action/submit")
    check("C3 submit 200", st == 200, str(report)[:100])
    check("C3 unsolved: total 0 / 29", report.get("total_earned") == 0 and report.get("total_possible") == 29,
          f"{report.get('total_earned')}/{report.get('total_possible')}")
    check("C3 passed=False (66% threshold)", report.get("passed") is False)
    sc = report.get("scorecard", [])
    check("C3 scorecard 10 rows, 5 k3d + 5 kubeadm",
          len([r for r in sc if r.get("context") == "k3d-cka"]) == 5 and
          len([r for r in sc if r.get("context") == "kubeadm-vms"]) == 5)
    check("C3 report file written", os.path.exists(f"/root/cka-labs/reports/report-{sid}.json"))

    # ---------- CANDIDATE: teardown after submit ----------
    time.sleep(3)
    check("C4 incus nodes deleted after submit",
          not [n for n in incus_names_all() if sid in n])
    check("C4 desktop deleted after submit", f"cka-desktop-{sid}" not in docker_names(),
          [n for n in docker_names() if "cka-desktop" in n])
    check("C4 k3d cluster deleted after submit", sid.replace("session-", "") not in k3d_clusters())

    # ---------- RESURRECTION REGRESSION ----------
    print("C5: resurrection regression (poll /api/session like the UI)...", flush=True)
    for _ in range(4):
        api("GET", "/api/session")
        time.sleep(2)
    api("GET", "/api/session")
    time.sleep(2)
    check("C5 no desktop resurrected for submitted session",
          f"cka-desktop-{sid}" not in docker_names(),
          [n for n in docker_names() if "cka-desktop" in n])

    # ---------- RECORDINGS: candidate events ----------
    print("C6: recording verification...", flush=True)
    evs = events_of(sid)
    etypes = {e.get("event") for e in evs}
    for expected in ("SESSION_START", "TASK_DEPLOYED", "TASK_JUMP", "TASK_FLAGGED", "TASK_RETRY", "EXAM_SUBMITTED"):
        check(f"C6 event {expected}", expected in etypes, "")
    jumps = [e for e in evs if e.get("event") == "TASK_JUMP"]
    check("C6 candidate actions actor=candidate", jumps and all(e.get("actor") == "candidate" for e in jumps),
          [(e.get("actor")) for e in jumps])
    check("C6 no ADMIN_* events in candidate session", not [e for e in evs if e.get("event", "").startswith("ADMIN_")])
    meta_path = os.path.join(RECORDINGS_DIR, f"{sid}.meta.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    check("C6 meta completed with scorecard", meta.get("status") == "completed" and meta.get("total_possible") == 29,
          f"{meta.get('status')} {meta.get('total_earned')}/{meta.get('total_possible')}")

    st, rec = api("GET", f"/api/recordings/{sid}")
    check("C6 admin can view recording detail", st == 200 and rec.get("session_id") == sid)
    # Visited tasks in this flow: 1 (start), 3 (jump/flag/retry), 7 (jump)
    check("C6 task timeline covers visited tasks", len(rec.get("task_timeline", [])) >= 3, len(rec.get("task_timeline", [])))
    st, evs_api = api("GET", f"/api/recordings/{sid}/events")
    check("C6 admin can view all events", st == 200 and evs_api.get("total", 0) == len(evs), evs_api.get("total"))
    st, recs = api("GET", "/api/recordings")
    check("C6 recordings list includes session", any(r.get("session_id") == sid for r in recs.get("recordings", [])))

    # ---------- ADMIN: action + actor marking ----------
    print("C7: admin terminate with actor marking...", flush=True)
    st, resp2 = api("POST", "/api/start", {"question_ids": ["SC-001", "WL-001", "TR-003"]})
    sid2 = resp2.get("session_id")
    check("C7 second session started", st == 200 and bool(sid2), str(resp2)[:80])
    time.sleep(8)
    st, infra = api("GET", "/api/admin/infrastructure", headers=ah)
    names = [r.get("name") for r in infra.get("resources", [])]
    check("C7 infra lists desktop+nodes+golden",
          f"cka-desktop-{sid2}" in names and "golden-k8s" in names and any(n.startswith("node1-") for n in names if n))
    st, term = api("POST", f"/api/admin/sessions/{sid2}/terminate", headers=ah)
    check("C7 admin terminate 200", st == 200, str(term)[:80])
    time.sleep(3)
    check("C7 terminate removed incus nodes", not [n for n in incus_names_all() if sid2 in n])
    check("C7 terminate removed desktop", f"cka-desktop-{sid2}" not in docker_names())
    evs2 = events_of(sid2)
    admin_evts = [e for e in evs2 if e.get("event", "").startswith("ADMIN_")]
    check("C7 ADMIN_SESSION_TERMINATE recorded", any(e.get("event") == "ADMIN_SESSION_TERMINATE" for e in evs2))
    check("C7 admin events actor=admin", admin_evts and all(e.get("actor") == "admin" for e in admin_evts))

    # admin logout + invalidation
    st, _ = api("POST", "/api/admin/logout", headers=ah)
    st, chk2 = api("GET", "/api/admin/check", headers=ah)
    check("C7 token invalidated after logout", chk2.get("authenticated") is False)

    print(f"\n=== API VERIFICATION v2 RESULT: {len(PASS)} passed, {len(FAIL)} failed ===", flush=True)
    if FAIL:
        print("FAILED:", FAIL, flush=True)
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(main())
