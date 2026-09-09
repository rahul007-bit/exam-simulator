"""
Race regression: browser VNC auto-reconnect (reconnect=true) hammering
/novnc/ws/desktop/{sid} while POST /api/action/submit grades + tears down.
Before the fix, a reconnect landing mid-teardown resurrected the desktop.
"""
import base64, json, os, socket, subprocess, threading, time, urllib.request, urllib.error

BASE = "http://127.0.0.1:3000"
QIDS = ["SC-001", "SC-005"]

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
        return e.code, {}

def ws_ping(host, port, path):
    try:
        s = socket.create_connection((host, port), timeout=3)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n"
               f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
               f"Sec-WebSocket-Version: 13\r\nSec-WebSocket-Protocol: binary\r\n\r\n")
        s.sendall(req.encode())
        s.recv(4096)
        s.close()
        return True
    except Exception:
        return False

stop = threading.Event()
pings = [0]

def vnc_loop(sid):
    while not stop.is_set():
        if ws_ping("127.0.0.1", 3000, f"/novnc/ws/desktop/{sid}"):
            pings[0] += 1
        time.sleep(0.6)

st, login = api("POST", "/api/admin/login", {"password": "admin123"})
ah = {"Authorization": f"Bearer {login.get('token', '')}"}
st, resp = api("POST", "/api/start", {"question_ids": QIDS})
sid = resp["session_id"]
print("session:", sid)
time.sleep(12)  # desktop up

r = subprocess.run(["docker", "ps", "--format", "{{.Names}} {{.Status}}"],
                   capture_output=True, text=True)
desk = [l for l in r.stdout.splitlines() if sid in l]
print("desktop before:", desk)

t = threading.Thread(target=vnc_loop, args=(sid,), daemon=True)
t.start()

t0 = time.time()
st, report = api("POST", "/api/action/submit")
print(f"submit {st} in {time.time()-t0:.0f}s")
time.sleep(20)  # keep hammering through grading + teardown
stop.set()
t.join(timeout=5)
print("vnc pings during window:", pings[0])

time.sleep(2)
r = subprocess.run(["docker", "ps", "-a", "--format", "{{.Names}} {{.Status}}"],
                   capture_output=True, text=True)
desk_after = [l for l in r.stdout.splitlines() if sid in l]
print("desktop after:", desk_after or "(none)")

r = subprocess.run(["incus", "list", "--format", "csv", "-c", "n"], capture_output=True, text=True)
left = [n for n in r.stdout.splitlines() if sid in n]
print("incus leftovers:", left or "(none)")

jr = subprocess.run(["journalctl", "-u", "k8s-web", "--since", "-3", "minutes",
                     "--no-pager", "-o", "short-iso"], capture_output=True, text=True)
ar = [l for l in jr.stdout.splitlines() if "AutoRestore" in l]
print("AutoRestore lines in window:", len(ar))
for l in ar:
    print("  ", l[:160])

ok = (not desk_after) and (not left) and (len(ar) == 0)
print("RACE_REGRESSION:", "PASS" if ok else "FAIL")
