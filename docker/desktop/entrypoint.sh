#!/bin/bash
set -e

# Clean up any stale X11 sockets or locks
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1 2>/dev/null

export DISPLAY=:1
export HOME=/home/exam
export USER=exam

# Create runtime dirs
mkdir -p /tmp/.X11-unix /home/exam/.vnc
chmod 1777 /tmp/.X11-unix
chown -R exam:exam /home/exam

# Configure xstartup for Openbox
cat << 'XSTARTUP' > /home/exam/.vnc/xstartup
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
exec openbox-session
XSTARTUP
chmod +x /home/exam/.vnc/xstartup
chown -R exam:exam /home/exam/.vnc

# Start TigerVNC as user exam
su - exam -c "vncserver :1 -geometry ${RESOLUTION:-1920x1080} -depth 24 -SecurityTypes None -localhost no --I-KNOW-THIS-IS-INSECURE"

# Wait for X11 to be ready
until su - exam -c "xdpyinfo -display :1" >/dev/null 2>&1; do
    sleep 0.2
done

# Start websockify on port 6080 for noVNC
websockify --web=/usr/share/novnc 6080 localhost:5901 &

# Start Redis desk-agent as exam user in background
su - exam -c "DISPLAY=:1 SESSION_ID='${SESSION_ID:-default}' REDIS_HOST='${REDIS_HOST:-172.17.0.1}' REDIS_PORT='${REDIS_PORT:-6379}' /usr/local/bin/desk-agent.py" &
AGENT_PID=$!

# Launch Firefox as user exam
su - exam -c "DISPLAY=:1 firefox-esr" &
FIREFOX_PID=$!

_shutdown() {
    echo "[Entrypoint] Stopping desktop container..."
    kill -TERM $AGENT_PID 2>/dev/null || true
    kill -TERM $FIREFOX_PID 2>/dev/null || true
    su - exam -c "vncserver -kill :1" 2>/dev/null || true
    exit 0
}

trap _shutdown SIGTERM SIGINT

wait
