#!/bin/bash
set -e

# Clean up any stale X11 sockets or locks
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1 2>/dev/null

export DISPLAY=:1
export HOME=/home/exam
export USER=exam

# Create runtime dirs
mkdir -p /tmp/.X11-unix /home/exam/.vnc /home/exam/.kube
chmod 1777 /tmp/.X11-unix

# Dynamically fetch kubeconfig and active task sheet from Redis if available
python3 - << 'PYEOF'
import os, redis

try:
    host = os.getenv("REDIS_HOST", "172.17.0.1")
    port = int(os.getenv("REDIS_PORT", "6379"))
    sid = os.getenv("SESSION_ID", "default")
    r = redis.Redis(host=host, port=port, socket_timeout=3)
    data = r.get(f"session:{sid}:kubeconfig") or r.get("k8s:kubeconfig")
    if data:
        with open("/home/exam/.kube/config", "wb") as f:
            f.write(data)
        print(f"[Entrypoint] Successfully configured kubeconfig from Redis (session: {sid})")
    else:
        print("[Entrypoint] No kubeconfig found in Redis, starting without cluster credentials")

    exam_md = r.get(f"session:{sid}:exam_md") or r.get("k8s:active_exam_md")
    if exam_md:
        with open("/home/exam/active_exam.md", "wb") as f:
            f.write(exam_md)
        print(f"[Entrypoint] Successfully injected active_exam.md from Redis")

    comp = r.get("cache:kubectl_completion")
    if comp:
        os.makedirs("/etc/bash_completion.d", exist_ok=True)
        with open("/etc/bash_completion.d/kubectl", "wb") as f:
            f.write(comp)
        print(f"[Entrypoint] Successfully injected pre-compiled kubectl completion from Redis")
except Exception as e:
    print(f"[Entrypoint] Warning: could not retrieve credentials/tasks from Redis: {e}")
PYEOF

chmod 600 /home/exam/.kube/config 2>/dev/null || true
chmod 644 /home/exam/active_exam.md 2>/dev/null || true

# Pre-seed Firefox profile to eliminate welcome screens, onboarding, and bloat
mkdir -p /home/exam/.mozilla/firefox/default.profile
cat << 'PREFS' > /home/exam/.mozilla/firefox/default.profile/prefs.js
user_pref("browser.startup.homepage", "https://kubernetes.io/docs/home/");
user_pref("browser.startup.page", 1);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("trailhead.firstrun.didSeeAboutWelcome", true);
user_pref("browser.newtabpage.enabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.snippets", false);
user_pref("browser.newtabpage.activity-stream.feeds.topsites", false);
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("browser.toolbars.bookmarks.visibility", "always");
PREFS

cat << 'PROFILES' > /home/exam/.mozilla/firefox/profiles.ini
[Profile0]
Name=default
IsRelative=1
Path=default.profile
Default=1

[General]
StartWithLastProfile=1
Version=2
PROFILES

chown -R exam:exam /home/exam

# Configure xstartup for XFCE4
cat << 'XSTARTUP' > /home/exam/.vnc/xstartup
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec dbus-launch --exit-with-session startxfce4
XSTARTUP
chmod +x /home/exam/.vnc/xstartup
chown -R exam:exam /home/exam/.vnc

# Start TigerVNC as user exam
su - exam -c "vncserver :1 -geometry ${RESOLUTION:-1920x1080} -depth 24 -SecurityTypes None -localhost no --I-KNOW-THIS-IS-INSECURE"

# Wait for X11 to be ready
until su - exam -c "xdpyinfo -display :1" >/dev/null 2>&1; do
    sleep 0.2
done

# Start TigerVNC native clipboard bridge as exam user
su - exam -c "DISPLAY=:1 vncconfig -nowin" &
VNCCONFIG_PID=$!

# Start websockify on port 6080 for noVNC
websockify --web=/usr/share/novnc 6080 localhost:5901 &

# Start Redis desk-agent as exam user in background
su - exam -c "DISPLAY=:1 SESSION_ID='${SESSION_ID:-default}' REDIS_HOST='${REDIS_HOST:-172.17.0.1}' REDIS_PORT='${REDIS_PORT:-6379}' /usr/local/bin/desk-agent.py" &
AGENT_PID=$!

# Launch XFCE Terminal & Firefox with Kubernetes Docs as user exam
su - exam -c "DISPLAY=:1 xfce4-terminal" &
TERM_PID=$!

su - exam -c "DISPLAY=:1 firefox-esr https://kubernetes.io/docs/home/" &
FIREFOX_PID=$!

_shutdown() {
    echo "[Entrypoint] Stopping desktop container..."
    kill -TERM $AGENT_PID 2>/dev/null || true
    kill -TERM $TERM_PID 2>/dev/null || true
    kill -TERM $FIREFOX_PID 2>/dev/null || true
    kill -TERM $VNCCONFIG_PID 2>/dev/null || true
    su - exam -c "vncserver -kill :1" 2>/dev/null || true
    exit 0
}

trap _shutdown SIGTERM SIGINT

wait

