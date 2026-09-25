import json, time, subprocess, urllib.request, urllib.error, os

BASE = "http://127.0.0.1:3000"
RECORDINGS_DIR = "/root/cka-labs/recordings"

def api(method, path, body=None, headers=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}

def run(args, timeout=60):
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()

PASS, FAIL = [], []
def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {str(detail)[:200]}", flush=True)

st, login = api("POST", "/api/admin/login", {"password": "admin123"})
ah = {"Authorization": f"Bearer {login.get('token', '')}"}
check("admin login", st == 200 and bool(login.get("token")))

st, resp = api("POST", "/api/start", {"question_ids": ["SC-001"]})
sid = resp.get("session_id")
print(f"session={sid}", flush=True)
check("session started", st == 200 and bool(sid))
container = f"cka-desktop-{sid}"

deadline = time.time() + 90
up = False
while time.time() < deadline:
    rc, out, _ = run(["docker", "ps", "--format", "{{.Names}}"])
    if container in [l.strip() for l in out.splitlines()]:
        up = True
        break
    time.sleep(2)
check("desktop container running", up, container)

def dex(cmd, timeout=60):
    return run(["docker", "exec", container, "bash", "-c", cmd], timeout=timeout)

# wait for desk-agent to actually start (entrypoint boots VNC first)
agent_up = False
deadline = time.time() + 60
while time.time() < deadline:
    rc, out, err = dex("pgrep -af desk-agent.py", timeout=15)
    if rc == 0 and "desk-agent.py" in out:
        agent_up = True
        break
    time.sleep(2)
check("desk-agent running", agent_up)

# wait for the terminal window
wid = ""
deadline = time.time() + 60
while time.time() < deadline:
    rc, out, err = dex("su - exam -c 'DISPLAY=:1 xdotool search --onlyvisible --class xfce4-terminal'")
    ids = [x.strip() for x in out.splitlines() if x.strip()]
    if ids:
        wid = ids[-1]
        break
    time.sleep(2)
check("xfce4-terminal window found", bool(wid), wid)

if wid:
    # Close Firefox so xfwm4 hands focus to the terminal. NOTE: do NOT use
    # `xdotool type --window` (XSendEvent = synthetic, invisible to the XI2 root
    # monitor) — type to the focused window via XTEST.
    dex("pkill -f firefox 2>/dev/null; sleep 2")
    time.sleep(1)
    dex(f"su - exam -c 'DISPLAY=:1 xdotool windowmap {wid}; DISPLAY=:1 xdotool windowraise {wid}; DISPLAY=:1 xdotool windowactivate --sync {wid}'")
    time.sleep(1.5)
    rc, out, _ = dex("su - exam -c 'DISPLAY=:1 xdotool getactivewindow getwindowname'")
    rc2, cls, _ = dex("su - exam -c 'DISPLAY=:1 xdotool getactivewindow getwindowclassname'")
    print(f"  info  focused window: {out}  class: {cls}", flush=True)
    check("terminal focused", ("terminal" in out.lower()) or ("terminal" in cls.lower()), f"{out} / {cls}")
    dex("su - exam -c 'DISPLAY=:1 xdotool type --delay 80 \"kubectl get nodes\"'")
    time.sleep(0.5); dex("su - exam -c 'DISPLAY=:1 xdotool key Return'"); time.sleep(1)
    dex("su - exam -c 'DISPLAY=:1 xdotool type --delay 80 \"echo hello-cka\"'")
    time.sleep(0.5); dex("su - exam -c 'DISPLAY=:1 xdotool key Return'"); time.sleep(1)
    dex("su - exam -c 'DISPLAY=:1 xdotool type --delay 80 \"sleep 99\"'")
    time.sleep(0.3); dex("su - exam -c 'DISPLAY=:1 xdotool key ctrl+c'"); time.sleep(3)
    dex("su - exam -c 'DISPLAY=:1 xdotool type --delay 80 \"echo abcX\"'")
    time.sleep(0.4); dex("su - exam -c 'DISPLAY=:1 xdotool key BackSpace'"); time.sleep(0.4)
    dex("su - exam -c 'DISPLAY=:1 xdotool key Return'"); time.sleep(3)

ev_path = os.path.join(RECORDINGS_DIR, f"{sid}.events.jsonl")
events = [json.loads(l) for l in open(ev_path) if l.strip()] if os.path.exists(ev_path) else []
dti = [e for e in events if e.get("event") == "DESKTOP_TERMINAL_INPUT"]
datas = [e.get("data") or {} for e in dti]
print(f"  info  total events={len(events)} desktop_input={len(dti)}", flush=True)
for d in datas:
    print("    DTI:", json.dumps({k: d.get(k) for k in ("text", "app", "window", "actor")}), flush=True)

texts = [(d.get("text") or "") for d in datas]
check("captured 'kubectl get nodes'", any("kubectl get nodes" in t for t in texts), texts)
check("captured 'echo hello-cka'", any("hello-cka" in t for t in texts), texts)
check("captured ctrl-c (^C)", any(t.endswith("^C") and "sleep 99" in t for t in texts), texts)
check("backspace applied (echo abc, not abcX)", any(t == "echo abc" for t in texts), texts)
check("app hint == terminal", bool(datas) and all(d.get("app") == "terminal" for d in datas),
      sorted({d.get("app") for d in datas}))
check("window title populated", bool(datas) and all(d.get("window") for d in datas),
      sorted({str(d.get("window"))[:40] for d in datas}))
check("actor stamped candidate", bool(dti) and all(e.get("actor") == "candidate" for e in dti))

print(f"=== DESKTOP INPUT E2E: {len(PASS)} pass, {len(FAIL)} fail (sid={sid}) ===", flush=True)
if FAIL:
    print("FAILED:", FAIL, flush=True)

st, term = api("POST", f"/api/admin/sessions/{sid}/terminate", {}, headers=ah)
print("terminate:", st, str(term)[:100], flush=True)
