/**
 * Kubernetes Exam Web Simulator - Admin Plane Controller
 */

let isAuthenticated = false;
let adminPresets = [];
let currentDefaultPreset = 'mock-01-acme';
let adminRefreshInterval = null;
let currentObserveSessionId = null;
let currentObserveTab = 'desktop';
let observeSessionSocket = null;
let observeTerm = null;
let observeTermSocket = null;
let observeFitAddon = null;

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

/* ==========================================================================
   Toast Notifications
   ========================================================================== */

function showToast(msg, duration = 3000) {
    const toast = document.getElementById('adminToast');
    if (!toast) return;
    toast.innerText = msg;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, duration);
}

function copyToClipboard(text, successMsg = 'Copied to clipboard!') {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(successMsg);
        }).catch(() => {
            promptFallback(text);
        });
    } else {
        promptFallback(text);
    }
}

function promptFallback(text) {
    window.prompt('Copy to clipboard: Ctrl+C, Enter', text);
}

/* ==========================================================================
   Authentication & State Management
   ========================================================================== */

async function checkAuth() {
    try {
        const res = await fetch('/api/admin/check');
        const data = await res.json();
        if (data.authenticated) {
            isAuthenticated = true;
            document.getElementById('viewLogin').style.display = 'none';
            document.getElementById('viewDashboard').style.display = 'block';
            document.getElementById('btnAdminLogout').style.display = 'inline-flex';
            document.getElementById('liveStatusIndicator').style.display = 'inline-flex';

            await loadPresetsAndConfig();
            await loadAdminSessions();

            if (!adminRefreshInterval) {
                adminRefreshInterval = setInterval(() => {
                    // Do not refresh table if currently in observe mode
                    if (!currentObserveSessionId) {
                        loadAdminSessions();
                    }
                }, 5000);
            }
        } else {
            showLoginView();
        }
    } catch (err) {
        console.error('Failed to check admin auth:', err);
        showLoginView();
    }
}

function showLoginView() {
    isAuthenticated = false;
    document.getElementById('viewLogin').style.display = 'flex';
    document.getElementById('viewDashboard').style.display = 'none';
    document.getElementById('btnAdminLogout').style.display = 'none';
    document.getElementById('liveStatusIndicator').style.display = 'none';
    if (adminRefreshInterval) {
        clearInterval(adminRefreshInterval);
        adminRefreshInterval = null;
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const pwInput = document.getElementById('inputAdminPassword');
    const errBox = document.getElementById('loginErrorMsg');
    const password = pwInput.value;

    errBox.style.display = 'none';
    errBox.innerText = '';

    try {
        const res = await fetch('/api/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password: password }),
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({ detail: 'Authentication failed' }));
            throw new Error(errData.detail || 'Incorrect admin password');
        }

        pwInput.value = '';
        await checkAuth();
    } catch (err) {
        errBox.innerText = err.message;
        errBox.style.display = 'block';
    }
}

async function adminLogout() {
    try {
        await fetch('/api/admin/logout', { method: 'POST' });
    } catch (_) {}
    showLoginView();
    showToast('Logged out successfully');
}

/* ==========================================================================
   Presets & Global Default Configuration
   ========================================================================== */

async function loadPresetsAndConfig() {
    try {
        const [presetsRes, configRes] = await Promise.all([
            fetch('/api/presets'),
            fetch('/api/admin/config'),
        ]);

        const presetsData = await presetsRes.json();
        const configData = await configRes.json();

        adminPresets = presetsData.presets || [];
        currentDefaultPreset = configData.default_preset || 'mock-01-acme';

        populatePresetSelects();
    } catch (err) {
        console.error('Failed to load presets or config:', err);
    }
}

function populatePresetSelects() {
    const defaultSelect = document.getElementById('selectDefaultPreset');
    const inviteSelect = document.getElementById('selectInvitePreset');

    defaultSelect.innerHTML = '';
    inviteSelect.innerHTML = '';

    adminPresets.forEach((p) => {
        const opt1 = document.createElement('option');
        opt1.value = p.filename;
        opt1.text = `${p.name} (${p.task_count || 0} tasks${p.time_limit_minutes ? `, ${p.time_limit_minutes}m` : ''})`;
        if (p.filename === currentDefaultPreset) opt1.selected = true;
        defaultSelect.appendChild(opt1);

        const opt2 = document.createElement('option');
        opt2.value = p.filename;
        opt2.text = opt1.text;
        if (p.filename === currentDefaultPreset) opt2.selected = true;
        inviteSelect.appendChild(opt2);
    });

    // Option for all 111 questions
    const optAll1 = document.createElement('option');
    optAll1.value = 'all';
    optAll1.text = 'Full Curriculum (All 111 Tasks, Untimed)';
    if (currentDefaultPreset === 'all') optAll1.selected = true;
    defaultSelect.appendChild(optAll1);

    const optAll2 = document.createElement('option');
    optAll2.value = 'all';
    optAll2.text = optAll1.text;
    if (currentDefaultPreset === 'all') optAll2.selected = true;
    inviteSelect.appendChild(optAll2);

    updateDefaultPresetMeta();
}

function updateDefaultPresetMeta() {
    const metaDiv = document.getElementById('defaultPresetMeta');
    const sel = document.getElementById('selectDefaultPreset').value;
    const found = adminPresets.find(p => p.filename === sel);
    if (found) {
        metaDiv.innerHTML = `Active default: <strong>${found.name}</strong> • ${found.task_count || 0} tasks • ${found.time_limit_minutes || 'Untimed'} mins`;
    } else if (sel === 'all') {
        metaDiv.innerHTML = `Active default: <strong>Full Curriculum</strong> • 111 tasks • Untimed`;
    } else {
        metaDiv.innerHTML = `Active default: <code>${sel}</code>`;
    }
}

async function saveDefaultPreset() {
    const sel = document.getElementById('selectDefaultPreset').value;
    if (!sel) return;

    try {
        const res = await fetch('/api/admin/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ default_preset: sel }),
        });

        if (!res.ok) throw new Error(await res.text());
        currentDefaultPreset = sel;
        updateDefaultPresetMeta();
        showToast(`Default preset set to: ${sel}`);
    } catch (err) {
        alert(`Failed to save default preset: ${err.message}`);
    }
}

/* ==========================================================================
   Candidate Invite Creation
   ========================================================================== */

async function generateCandidateInvite() {
    const sel = document.getElementById('selectInvitePreset').value;
    try {
        const res = await fetch('/api/admin/sessions/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ preset: sel }),
        });

        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();

        const fullUrl = `${window.location.origin}/?token=${data.token}`;
        const outputBox = document.getElementById('inviteOutputBox');
        const linkDisplay = document.getElementById('inviteLinkDisplay');
        const badge = document.getElementById('invitePresetBadge');

        badge.innerText = data.preset;
        linkDisplay.innerText = fullUrl;
        outputBox.style.display = 'block';

        copyToClipboard(fullUrl, 'Candidate link generated & copied!');
        await loadAdminSessions();
    } catch (err) {
        alert(`Failed to create invite: ${err.message}`);
    }
}

function copyGeneratedInviteLink() {
    const linkDisplay = document.getElementById('inviteLinkDisplay');
    if (linkDisplay && linkDisplay.innerText) {
        copyToClipboard(linkDisplay.innerText, 'Invite link copied to clipboard!');
    }
}

/* ==========================================================================
   Live Candidate Sessions & Invites Table
   ========================================================================== */

async function loadAdminSessions() {
    const tbody = document.getElementById('adminSessionsTableBody');
    try {
        const res = await fetch('/api/admin/sessions');
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        const items = data.sessions || [];

        if (items.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; color: #64748b; padding: 28px;">
                        No candidate sessions or invites recorded yet. Generate an invite above to begin!
                    </td>
                </tr>
            `;
            return;
        }

        let html = '';
        items.forEach(item => {
            const sid = item.session_id || '';
            const tok = item.candidate_token || '';
            const status = (item.status || 'unknown').toLowerCase();
            const isRunning = !!item.container_running;
            const fullLink = item.url ? (item.url.startsWith('http') ? item.url : `${window.location.origin}${item.url}`) : '';

            // Status Pill
            let statusClass = 'status-ended';
            let statusIcon = '⚫';
            if (status === 'active') {
                statusClass = 'status-active';
                statusIcon = '🟢';
            } else if (status === 'pending') {
                statusClass = 'status-pending';
                statusIcon = '🟡';
            }
            const statusPill = `<span class="status-pill ${statusClass}">${statusIcon} ${status}</span>`;

            // Container State
            let containerBadge = '<span class="container-badge container-na">N/A</span>';
            if (sid) {
                if (isRunning) {
                    containerBadge = '<span class="container-badge container-running">● Running</span>';
                } else {
                    containerBadge = '<span class="container-badge container-stopped">■ Stopped</span>';
                }
            }

            // Time remaining
            let timeStr = '—';
            if (status === 'active') {
                if (typeof item.time_remaining_seconds === 'number') {
                    const rem = item.time_remaining_seconds;
                    const h = Math.floor(rem / 3600);
                    const m = Math.floor((rem % 3600) / 60);
                    const s = rem % 60;
                    timeStr = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
                } else {
                    timeStr = 'Untimed';
                }
            } else if (status === 'pending') {
                timeStr = 'Waiting for start';
            } else {
                timeStr = 'Ended';
            }

            // Created Date
            let createdFormatted = item.created_at || '—';
            if (item.created_at && item.created_at.includes('T')) {
                try {
                    const dt = new Date(item.created_at);
                    createdFormatted = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' ' + dt.toLocaleDateString();
                } catch (_) {}
            }

            // Actions
            let actionsHtml = `<div class="table-actions">`;
            if (fullLink) {
                actionsHtml += `
                    <button class="btn btn-secondary btn-sm" title="Copy Candidate Invite Link" onclick="copyToClipboard('${fullLink}', 'Candidate link copied!')">
                        Copy Link
                    </button>
                `;
            }
            if (status === 'active' && sid) {
                actionsHtml += `
                    <button class="btn btn-observe btn-sm" title="Observe Candidate in View-Only Mode" onclick="openObserveView('${sid}', '${tok}', '${escapeHtml(item.name || '')}')">
                        👁 Observe
                    </button>
                `;
            }
            const termIdentifier = sid || tok;
            if (status === 'active' || status === 'pending') {
                actionsHtml += `
                    <button class="btn btn-terminate btn-sm" title="Terminate or Cancel Session" onclick="terminateSessionPrompt('${termIdentifier}')">
                        ⏹ End
                    </button>
                `;
            }
            actionsHtml += `</div>`;

            const displaySid = sid ? `<span class="code-cell" onclick="copyToClipboard('${sid}')" title="Click to copy">${sid.slice(0, 14)}...</span>` : '<span style="color:#64748b;">Pending</span>';
            const displayTok = tok ? `<span class="code-cell" style="color:#38bdf8;" onclick="copyToClipboard('${tok}')" title="Click to copy">${tok.slice(0, 12)}...</span>` : '—';

            html += `
                <tr>
                    <td>${displaySid}</td>
                    <td>${displayTok}</td>
                    <td><strong>${escapeHtml(item.name || 'Exam')}</strong></td>
                    <td>${statusPill}</td>
                    <td>${containerBadge}</td>
                    <td style="font-family: var(--font-code); font-weight: 600;">${timeStr}</td>
                    <td style="font-size: 0.78rem; color: #94a3b8;">${createdFormatted}</td>
                    <td>${actionsHtml}</td>
                </tr>
            `;
        });

        tbody.innerHTML = html;
    } catch (err) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: #ef4444; padding: 20px;">
                    Error loading candidate sessions: ${escapeHtml(err.message)}
                </td>
            </tr>
        `;
    }
}

async function terminateSessionPrompt(identifier) {
    if (!identifier) return;
    if (!confirm(`Are you sure you want to terminate or cancel session/invite: ${identifier}?`)) {
        return;
    }
    try {
        const res = await fetch(`/api/admin/sessions/${encodeURIComponent(identifier)}/terminate`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        showToast(`Session ${identifier} terminated`);
        await loadAdminSessions();
    } catch (err) {
        alert(`Failed to terminate: ${err.message}`);
    }
}

/* ==========================================================================
   Observe Mode (Live View-Only VNC + Admin Shell)
   ========================================================================== */

async function openObserveView(sessionId, candidateToken, presetName) {
    currentObserveSessionId = sessionId;
    const overlay = document.getElementById('viewObserve');
    overlay.classList.add('active');

    document.getElementById('observeSessionIdBadge').innerText = `#${sessionId}`;
    document.getElementById('observeTokenBadge').innerText = candidateToken ? `Token: ${candidateToken.slice(0, 10)}...` : '';

    // Load initial candidate details and start stream
    await refreshObserveData(sessionId);

    // Set view-only VNC iframe
    const vncFrame = document.getElementById('observeVncFrame');
    const vncUrl = `/novnc/vnc.html?autoconnect=true&resize=remote&reconnect=true&view_only=true&path=ws/desktop/${encodeURIComponent(sessionId)}`;
    vncFrame.src = vncUrl;

    // Connect to real-time session WS
    connectObserveSessionWs(sessionId);

    // Default to desktop view
    switchObserveTab('desktop');
}

async function refreshObserveData(sessionId) {
    try {
        const res = await fetch(`/api/admin/session/${encodeURIComponent(sessionId)}`);
        if (!res.ok) return;
        const data = await res.json();

        // Header and task badges
        const curTask = data.current_task;
        if (curTask) {
            document.getElementById('observeTaskHeader').innerText = `Task ${curTask.task_num} Instructions`;
            document.getElementById('observeTaskProgressBadge').innerText = `Task ${curTask.task_num} of ${data.total_tasks}`;
            document.getElementById('observeBadgePoints').innerText = `${curTask.points || 0} pts`;
            document.getElementById('observeBadgeContext').innerText = `context: ${curTask.target_context || 'k3d-cka'}`;
            document.getElementById('observeBadgeNamespace').innerText = `ns: ${curTask.namespace || 'default'}`;
            document.getElementById('observeTaskTitle').innerText = curTask.title || 'Task Details';

            const mdContent = curTask.description || 'No task description available.';
            if (window.marked) {
                document.getElementById('observeTaskMarkdown').innerHTML = marked.parse(mdContent);
            } else {
                document.getElementById('observeTaskMarkdown').innerText = mdContent;
            }
        }

        // Render full task list
        const listDiv = document.getElementById('observeTaskList');
        if (listDiv && data.questions) {
            listDiv.innerHTML = data.questions.map(q => {
                const isCurrent = !!q.is_current;
                const isFlagged = !!q.is_flagged;
                let bg = isCurrent ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255, 255, 255, 0.03)';
                let border = isCurrent ? '1px solid var(--accent-blue)' : '1px solid transparent';
                return `
                    <div style="padding: 6px 10px; border-radius: 4px; background: ${bg}; border: ${border}; font-size: 0.76rem; display: flex; justify-content: space-between; align-items: center;">
                        <span><strong>#${q.task_num}</strong> ${escapeHtml(q.title)}</span>
                        <span>${isFlagged ? '🚩' : ''} ${q.points}pts</span>
                    </div>
                `;
            }).join('');
        }

    } catch (err) {
        console.error('Failed to load observe details:', err);
    }
}

function connectObserveSessionWs(sessionId) {
    if (observeSessionSocket) {
        try { observeSessionSocket.close(); } catch (_) {}
    }
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/session/${encodeURIComponent(sessionId)}`;
    try {
        observeSessionSocket = new WebSocket(wsUrl);
        observeSessionSocket.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === 'timer_tick' && typeof msg.time_remaining_seconds === 'number') {
                    const rem = msg.time_remaining_seconds;
                    const h = Math.floor(rem / 3600);
                    const m = Math.floor((rem % 3600) / 60);
                    const s = rem % 60;
                    document.getElementById('observeTimerDisplay').innerText =
                        `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
                } else if (msg.type === 'transition_progress') {
                    // Task transition occurred, refresh candidate task details
                    refreshObserveData(sessionId);
                }
            } catch (_) {}
        };
    } catch (_) {}
}

function switchObserveTab(tab) {
    currentObserveTab = tab;
    const btnDesktop = document.getElementById('btnObserveTabDesktop');
    const btnTerminal = document.getElementById('btnObserveTabTerminal');
    const vncFrame = document.getElementById('observeVncFrame');
    const termContainer = document.getElementById('observeTerminalContainer');

    if (tab === 'desktop') {
        btnDesktop.classList.add('active');
        btnTerminal.classList.remove('active');
        vncFrame.style.display = 'block';
        termContainer.style.display = 'none';
    } else {
        btnTerminal.classList.add('active');
        btnDesktop.classList.remove('active');
        vncFrame.style.display = 'none';
        termContainer.style.display = 'block';
        initObserveTerminal(currentObserveSessionId);
    }
}

function initObserveTerminal(sessionId) {
    if (observeTerm) {
        if (observeFitAddon) {
            setTimeout(() => { observeFitAddon.fit(); }, 50);
        }
        return;
    }

    const container = document.getElementById('observeTerminalContainer');
    container.innerHTML = '';

    if (!window.Terminal) return;

    observeTerm = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: "'Fira Code', monospace",
        theme: {
            background: '#0b0f19',
            foreground: '#e2e8f0',
            cursor: '#38bdf8',
        },
    });

    if (window.FitAddon && window.FitAddon.FitAddon) {
        observeFitAddon = new window.FitAddon.FitAddon();
        observeTerm.loadAddon(observeFitAddon);
    }

    observeTerm.open(container);
    if (observeFitAddon) {
        setTimeout(() => { observeFitAddon.fit(); }, 50);
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/terminal/${encodeURIComponent(sessionId)}`;
    observeTermSocket = new WebSocket(wsUrl);
    observeTermSocket.binaryType = 'arraybuffer';

    observeTermSocket.onopen = () => {
        observeTerm.write('\r\n\x1b[32m[Admin Plane Connected to Session Container]\x1b[0m\r\n');
        if (observeFitAddon) {
            observeFitAddon.fit();
            const dims = { resize: { cols: observeTerm.cols, rows: observeTerm.rows } };
            observeTermSocket.send(JSON.stringify(dims));
        }
    };

    observeTermSocket.onmessage = (e) => {
        if (e.data instanceof ArrayBuffer) {
            observeTerm.write(new Uint8Array(e.data));
        } else {
            observeTerm.write(e.data);
        }
    };

    observeTerm.onData((data) => {
        if (observeTermSocket && observeTermSocket.readyState === WebSocket.OPEN) {
            observeTermSocket.send(data);
        }
    });

    window.addEventListener('resize', () => {
        if (observeFitAddon && currentObserveTab === 'terminal') {
            observeFitAddon.fit();
            if (observeTermSocket && observeTermSocket.readyState === WebSocket.OPEN) {
                const dims = { resize: { cols: observeTerm.cols, rows: observeTerm.rows } };
                observeTermSocket.send(JSON.stringify(dims));
            }
        }
    });
}

function closeObserveView() {
    currentObserveSessionId = null;
    const overlay = document.getElementById('viewObserve');
    overlay.classList.remove('active');

    const vncFrame = document.getElementById('observeVncFrame');
    vncFrame.src = 'about:blank';

    if (observeSessionSocket) {
        try { observeSessionSocket.close(); } catch (_) {}
        observeSessionSocket = null;
    }

    if (observeTermSocket) {
        try { observeTermSocket.close(); } catch (_) {}
        observeTermSocket = null;
    }

    if (observeTerm) {
        try { observeTerm.dispose(); } catch (_) {}
        observeTerm = null;
        observeFitAddon = null;
    }

    loadAdminSessions();
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, function (m) {
        switch (m) {
            case '&': return '&amp;';
            case '<': return '&lt;';
            case '>': return '&gt;';
            case '"': return '&quot;';
            case "'": return '&#039;';
            default: return m;
        }
    });
}
