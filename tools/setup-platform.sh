#!/usr/bin/env bash
# ==============================================================================
# CKA Exam Platform Provisioning Script
# ==============================================================================
# Sets up a fresh Ubuntu (22.04 or 24.04 LTS) VM as an ultra-lightweight,
# high-performance Kubernetes exam simulator host:
#   1. Ultra-lightweight XFCE4 desktop (compositing disabled, zero bloat)
#   2. Native DEB Mozilla Firefox (official Mozilla repo, no snap confinement)
#   3. TigerVNC (:1, port 5901) + noVNC Web Proxy (port 6080)
#   4. Bidirectional host <-> VNC clipboard bridge (autocutsel + vncconfig + xsel)
#   5. Browser keyboard lock (locks Esc/Tab for vim/nano in remote desktop)
#   6. Candidate user ('exam') with passwordless sudo and desktop launchers
#   7. Simulator web service ('k8s-web.service' on port 3000)
#   8. OS performance tuning (background timer & bloat service disabling)
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }

if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (use sudo)."
    exit 1
fi

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
log_info "Deploying CKA Exam Simulator Platform from: ${APP_DIR}"

# ------------------------------------------------------------------------------
# 1. System Update & Bloat Removal
# ------------------------------------------------------------------------------
log_info "Updating package lists and purging desktop bloat..."
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq

# Purge conflicting window managers, display managers, and audio/printer bloat
apt-get purge -y -qq \
    openbox \
    sddm \
    lubuntu-* \
    lxqt-* \
    alacritty \
    speech-dispatcher \
    orca \
    blueman \
    printer-driver-* \
    cups* \
    spice-vdagent \
    2>/dev/null || true

apt-get autoremove -y -qq --purge 2>/dev/null || true

# ------------------------------------------------------------------------------
# 2. Core Platform Packages Installation
# ------------------------------------------------------------------------------
log_info "Installing lightweight desktop and VNC stack..."
apt-get install -y -qq \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    tigervnc-standalone-server \
    novnc \
    websockify \
    autocutsel \
    xsel \
    xclip \
    curl \
    jq \
    nano \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-yaml

# ------------------------------------------------------------------------------
# 2.5 Container Engine (Docker) & Kubernetes Tools (k3d, kubectl)
# ------------------------------------------------------------------------------
log_info "Installing Docker, k3d, and kubectl..."
apt-get install -y -qq docker.io
systemctl enable --now docker

if ! command -v k3d >/dev/null 2>&1; then
    log_info "Installing k3d..."
    curl -fsSL https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash
fi

if ! command -v kubectl >/dev/null 2>&1; then
    log_info "Installing kubectl..."
    curl -fsSL -o /usr/local/bin/kubectl "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
    chmod +x /usr/local/bin/kubectl
fi

# ------------------------------------------------------------------------------
# 3. Fix Ubuntu 24.04 AppArmor User Namespace Restrictions (for Firefox & Tools)
# ------------------------------------------------------------------------------
log_info "Configuring kernel unprivileged user namespace permissions..."
cat << 'EOF' > /etc/sysctl.d/99-disable-userns-restriction.conf
# Allow unprivileged user namespaces for browser sandboxes inside VNC
kernel.apparmor_restrict_unprivileged_userns = 0
EOF
sysctl --system >/dev/null 2>&1 || true

# ------------------------------------------------------------------------------
# 4. Native DEB Mozilla Firefox Installation (Official Mozilla APT Repo)
# ------------------------------------------------------------------------------
log_info "Configuring official Mozilla APT repository for native Firefox..."
# Remove Ubuntu snap firefox if installed (snap cgroups fail inside VNC services)
if command -v snap >/dev/null 2>&1; then
    snap remove firefox 2>/dev/null || true
fi

install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://packages.mozilla.org/apt/repo-signing-key.gpg -o /etc/apt/keyrings/packages.mozilla.org.asc

cat << 'EOF' > /etc/apt/sources.list.d/mozilla.list
deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main
EOF

# Prioritize native DEB packages over Ubuntu snap wrapper
cat << 'EOF' > /etc/apt/preferences.d/mozilla
Package: *
Pin: origin packages.mozilla.org
Pin-Priority: 1000

Package: firefox*
Pin: release o=Ubuntu*
Pin-Priority: -1
EOF

apt-get update -qq
apt-get install -y -qq firefox

# ------------------------------------------------------------------------------
# 5. Candidate User & Host Admin Setup
# ------------------------------------------------------------------------------
EXAM_USER="${EXAM_USER:-exam}"
ADMIN_USER="${ADMIN_USER:-${SUDO_USER:-}}"

log_info "Configuring candidate user '${EXAM_USER}'..."
if ! id -u "${EXAM_USER}" >/dev/null 2>&1; then
    useradd -m -s /bin/bash -u 1000 "${EXAM_USER}" 2>/dev/null || useradd -m -s /bin/bash "${EXAM_USER}"
fi

# Candidate user is in docker group for container drills, but NOT in sudo group
usermod -aG docker "${EXAM_USER}" 2>/dev/null || true
gpasswd -d "${EXAM_USER}" sudo 2>/dev/null || true

# Strictly whitelisted sudo for candidate examctl commands (prevents host tampering)
cat << EOF > /etc/sudoers.d/examctl
${EXAM_USER} ALL=(root) NOPASSWD: /root/cka-labs/labctl tasks, /root/cka-labs/labctl status, /root/cka-labs/labctl next, /root/cka-labs/labctl prev, /root/cka-labs/labctl jump *, /root/cka-labs/labctl flag, /root/cka-labs/labctl flag *, /root/cka-labs/labctl unflag, /root/cka-labs/labctl unflag *, /root/cka-labs/labctl record-shell, /root/cka-labs/labctl record-shell *
EOF
chmod 0440 /etc/sudoers.d/examctl
rm -f /etc/sudoers.d/exam

# Configure host admin user sudo access if present
if [ -n "${ADMIN_USER}" ] && id -u "${ADMIN_USER}" >/dev/null 2>&1 && [ "${ADMIN_USER}" != "${EXAM_USER}" ] && [ "${ADMIN_USER}" != "root" ]; then
    usermod -aG sudo,docker "${ADMIN_USER}" 2>/dev/null || true
    cat << EOF > "/etc/sudoers.d/${ADMIN_USER}"
${ADMIN_USER} ALL=(ALL) NOPASSWD:ALL
EOF
    chmod 0440 "/etc/sudoers.d/${ADMIN_USER}"
fi

# Copy full exam .bashrc with kubectl aliases, shortcuts, and banner
if [ -f "${APP_DIR}/tools/exam_bashrc" ]; then
    cp -f "${APP_DIR}/tools/exam_bashrc" "/home/${EXAM_USER}/.bashrc"
    chown "${EXAM_USER}:${EXAM_USER}" "/home/${EXAM_USER}/.bashrc"
fi

# Install examctl candidate CLI
if [ -f "${APP_DIR}/tools/examctl" ]; then
    cp -f "${APP_DIR}/tools/examctl" /usr/local/bin/examctl
    chmod +x /usr/local/bin/examctl
fi

# Configure candidate SSH key and node aliases (ssh node1, node2)
install -d -m 0700 -o exam -g exam /home/exam/.ssh
if [ ! -f /home/exam/.ssh/id_ed25519 ]; then
    su - exam -c "ssh-keygen -t ed25519 -N '' -f /home/exam/.ssh/id_ed25519 -q"
fi

# Link candidate user and platform host to remote kubeadm cluster
if [ -f "${APP_DIR}/tools/link-exam-nodes.sh" ]; then
    log_info "Linking candidate 'exam' and host to remote kubeadm cluster..."
    chmod +x "${APP_DIR}/tools/link-exam-nodes.sh"
    bash "${APP_DIR}/tools/link-exam-nodes.sh" || log_warn "Node linking had warnings."
fi

# ------------------------------------------------------------------------------
# 6. XFCE4 Desktop & TigerVNC Configuration
# ------------------------------------------------------------------------------
log_info "Configuring XFCE4 desktop without compositing and with clipboard bridge..."
install -d -m 0700 -o exam -g exam /home/exam/.vnc
install -d -m 0755 -o exam -g exam /home/exam/Desktop
install -d -m 0755 -o exam -g exam /home/exam/.config/xfce4/xfconf/xfce-perchannel-xml

# VNC Xstartup script: activates autocutsel for both CLIPBOARD & PRIMARY, and vncconfig
cat << 'EOF' > /home/exam/.vnc/xstartup
#!/bin/sh
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
export XKL_XMODMAP_DISABLE=1
autocutsel -fork
autocutsel -selection PRIMARY -fork
vncconfig -nowin &
exec startxfce4
EOF
chmod +x /home/exam/.vnc/xstartup
chown exam:exam /home/exam/.vnc/xstartup

# Disable software compositing in xfwm4 (eliminates LLVMpipe CPU waste & lag)
cat << 'EOF' > /home/exam/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml
<?xml version="1.1" encoding="UTF-8"?>
<channel name="xfwm4" version="1.0">
  <property name="general" type="empty">
    <property name="use_compositing" type="bool" value="false"/>
    <property name="borderless_maximize" type="bool" value="true"/>
    <property name="click_to_focus" type="bool" value="true"/>
  </property>
</channel>
EOF
chown -R exam:exam /home/exam/.config

# Desktop Launchers
cat << 'EOF' > /home/exam/Desktop/terminal.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Terminal
Comment=Xfce Terminal
Exec=/usr/local/bin/xfce4-terminal
Icon=org.xfce.terminal
Terminal=false
Categories=System;TerminalEmulator;
EOF

cat << 'EOF' > /home/exam/Desktop/firefox.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Firefox Web Browser
Comment=Access the Web
Exec=/usr/bin/firefox %u
Icon=firefox
Terminal=false
Categories=Network;WebBrowser;
EOF

chmod +x /home/exam/Desktop/*.desktop
chown -R exam:exam /home/exam/Desktop

# System-wide wrapper for xfce4-terminal to ensure ANY launch (dock, menu, shortcut) is recorded
cat << 'EOF' > /usr/local/bin/xfce4-terminal
#!/usr/bin/env bash
if [ -z "$EXAM_RECORDED" ]; then
    export EXAM_RECORDED=1
    exec /usr/bin/xfce4-terminal -e "sudo /root/cka-labs/labctl record-shell" "$@"
else
    exec /usr/bin/xfce4-terminal "$@"
fi
EOF
chmod 0755 /usr/local/bin/xfce4-terminal

# ------------------------------------------------------------------------------
# 7. noVNC Patches: Keyboard Lock & Bidirectional Clipboard Bridge
# ------------------------------------------------------------------------------
log_info "Patching /usr/share/novnc/vnc.html for keyboard lock & clipboard bridge..."
NOVNC_HTML="/usr/share/novnc/vnc.html"

if [ -f "$NOVNC_HTML" ]; then
    # Backup original
    [ -f "${NOVNC_HTML}.orig" ] || cp "$NOVNC_HTML" "${NOVNC_HTML}.orig"

    python3 -c "
with open('$NOVNC_HTML', 'r', encoding='utf-8') as f:
    content = f.read()

patch = '''
    <!-- Full Keyboard Lock Acquisition -->
    <script>
    (function() {
        function acquireKeyboardLock() {
            if (navigator.keyboard && navigator.keyboard.lock) {
                navigator.keyboard.lock(['Escape', 'Tab', 'AltLeft', 'AltRight', 'ControlLeft', 'ControlRight']).catch(function(){});
            }
        }
        window.addEventListener('load', acquireKeyboardLock);
        window.addEventListener('focus', acquireKeyboardLock);
        window.addEventListener('click', acquireKeyboardLock);
        window.addEventListener('pointerdown', acquireKeyboardLock);
        document.addEventListener('keydown', function(e) { acquireKeyboardLock(); }, true);
    })();
    </script>

    <!-- Host <-> VNC Bidirectional Clipboard Bridge -->
    <script>
    (function() {
        var lastSent = '';
        var lastReceived = '';
        function getRfb() { return (window.UI && window.UI.rfb) || window.rfb; }

        window.addEventListener('message', function(e) {
            if (!e.data) return;
            if (e.data.type === 'SET_CLIPBOARD' && typeof e.data.text === 'string') {
                var text = e.data.text;
                if (!text || text === lastSent) return;
                lastSent = text;
                var rfb = getRfb();
                if (rfb && rfb.clipboardPasteFrom) {
                    try { rfb.clipboardPasteFrom(text); } catch(err) {}
                }
                var clipBox = document.getElementById('noVNC_clipboard_text');
                if (clipBox) clipBox.value = text;
            }
        });

        window.addEventListener('paste', function(e) {
            var text = (e.clipboardData || window.clipboardData).getData('text');
            if (text) {
                var rfb = getRfb();
                if (rfb && rfb.clipboardPasteFrom) {
                    rfb.clipboardPasteFrom(text);
                    lastSent = text;
                }
                var clipBox = document.getElementById('noVNC_clipboard_text');
                if (clipBox) clipBox.value = text;
            }
        });

        function attachRfbClipboard() {
            var rfb = getRfb();
            if (!rfb) { setTimeout(attachRfbClipboard, 500); return; }
            rfb.addEventListener('clipboard', function(ev) {
                if (ev && ev.detail && typeof ev.detail.text === 'string') {
                    var text = ev.detail.text;
                    if (!text || text === lastReceived) return;
                    lastReceived = text;
                    try { window.parent.postMessage({ type: 'VNC_CLIPBOARD', text: text }, '*'); } catch(_) {}
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(text).catch(function() {});
                    }
                }
            });
        }
        attachRfbClipboard();

        window.addEventListener('focus', function() {
            if (navigator.clipboard && navigator.clipboard.readText) {
                navigator.clipboard.readText().then(function(text) {
                    if (text && text !== lastSent && text !== lastReceived) {
                        lastSent = text;
                        var rfb = getRfb();
                        if (rfb && rfb.clipboardPasteFrom) { rfb.clipboardPasteFrom(text); }
                    }
                }).catch(function() {});
            }
        });
    })();
    </script>
'''

if 'Host <-> VNC Bidirectional Clipboard Bridge' not in content:
    content = content.replace('</body>', patch + '\n </body>')
    with open('$NOVNC_HTML', 'w', encoding='utf-8') as f:
        f.write(content)
    print('vnc.html successfully patched.')
else:
    print('vnc.html is already patched.')
"
fi

# ------------------------------------------------------------------------------
# 8. Python Virtual Environment Setup (Simulator Web App)
# ------------------------------------------------------------------------------
log_info "Configuring Python virtual environment in ${APP_DIR}..."
if [ ! -d "${APP_DIR}/.venv" ]; then
    python3 -m venv "${APP_DIR}/.venv"
fi

"${APP_DIR}/.venv/bin/pip" install --upgrade pip -q
if [ -f "${APP_DIR}/requirements.txt" ]; then
    "${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt" -q
fi
"${APP_DIR}/.venv/bin/pip" install uvicorn fastapi pyyaml -q

# ------------------------------------------------------------------------------
# 9. Systemd Services Deployment
# ------------------------------------------------------------------------------
log_info "Creating and enabling systemd services..."

# 1. TigerVNC Server Service
cat << 'EOF' > /etc/systemd/system/exam-vnc.service
[Unit]
Description=TigerVNC Server for Exam User
After=network.target

[Service]
Type=simple
User=exam
Environment=HOME=/home/exam
Environment=USER=exam
ExecStartPre=-/usr/bin/vncserver -kill :1
ExecStart=/usr/bin/vncserver :1 -fg -geometry 1920x1080 -depth 16 -SecurityTypes None -localhost yes -AlwaysShared --I-KNOW-THIS-IS-INSECURE
ExecStop=/usr/bin/vncserver -kill :1
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 2. noVNC Websockify Proxy Service
cat << 'EOF' > /etc/systemd/system/exam-novnc.service
[Unit]
Description=noVNC Web Proxy (Websockify)
After=network.target exam-vnc.service

[Service]
Type=simple
User=root
ExecStart=/usr/bin/websockify --web /usr/share/novnc 6080 127.0.0.1:5901
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 3. Simulator Web Server Service
cat << EOF > /etc/systemd/system/k8s-web.service
[Unit]
Description=Kubernetes Exam Web Simulator
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
Environment=EXAM_PRESET=medium-02-security-workloads
Environment=EXAM_ADMIN=0
Environment=VNC_DISPLAY=:1
Environment=XAUTHORITY=/home/exam/.Xauthority
Environment=EXAM_HOME=/home/exam
ExecStart=${APP_DIR}/.venv/bin/uvicorn web.server:app --host 0.0.0.0 --port 3000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload and start services
systemctl daemon-reload
systemctl enable --now exam-vnc.service
systemctl enable --now exam-novnc.service
systemctl enable --now k8s-web.service
systemctl restart exam-vnc.service exam-novnc.service k8s-web.service

# ------------------------------------------------------------------------------
# 10. Performance Optimization (Stop Spikes & Lockups)
# ------------------------------------------------------------------------------
log_info "Disabling disruptive background OS timers and auto-update checks..."
systemctl mask unattended-upgrades.service 2>/dev/null || true
systemctl mask apt-daily.timer apt-daily-upgrade.timer 2>/dev/null || true
systemctl mask motd-news.timer 2>/dev/null || true
systemctl disable --now bluetooth.service ModemManager.service 2>/dev/null || true

cat << 'EOF' > /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
APT::Periodic::Unattended-Upgrade "0";
EOF

# ------------------------------------------------------------------------------
# 11. Verification & Summary
# ------------------------------------------------------------------------------
log_info "Verifying services..."
sleep 2

VNC_OK=$(ss -tulpn | grep -q ":5901" && echo "YES" || echo "NO")
NOVNC_OK=$(ss -tulpn | grep -q ":6080" && echo "YES" || echo "NO")
WEB_OK=$(ss -tulpn | grep -q ":3000" && echo "YES" || echo "NO")

echo ""
echo "=========================================================================="
log_success "CKA Exam Simulator Platform Setup Complete!"
echo "=========================================================================="
echo "  • TigerVNC Server (:1):   5901 -> [Status: ${VNC_OK}]"
echo "  • noVNC Web Proxy:        6080 -> [Status: ${NOVNC_OK}]"
echo "  • Simulator Web App:      3000 -> [Status: ${WEB_OK}]"
echo ""
echo "Access URLs:"
echo "  Candidate View: http://<VM-IP>:3000"
echo "  Admin View:     http://<VM-IP>:3000?admin=1"
echo "  Direct Desktop: http://<VM-IP>:6080/vnc.html?autoconnect=true&resize=remote"
echo ""
echo "Credentials:"
echo "  VNC / Desktop User: 'exam' (Password: 'exam', NOPASSWD sudo)"
echo "=========================================================================="
