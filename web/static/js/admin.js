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
            await loadSystemResources();
            await loadAdminSessions();
            await loadAdminInfrastructure();

            if (!adminRefreshInterval) {
                adminRefreshInterval = setInterval(() => {
                    // Do not refresh table if currently in observe mode
                    if (!currentObserveSessionId) {
                        loadAdminSessions();
                        loadSystemResources();
                        loadAdminInfrastructure();
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

/* ==========================================================================
   Server Capacity & Resource Limits
   ========================================================================== */

async function loadSystemResources() {
    try {
        const res = await fetch('/api/admin/resources');
        if (!res.ok) return;
        const data = await res.json();

        // 1. RAM Usage
        const totalGb = (data.total_mem_mb / 1024).toFixed(1);
        const usedGb = (data.used_mem_mb / 1024).toFixed(1);
        const percent = data.total_mem_mb > 0 ? Math.round((data.used_mem_mb / data.total_mem_mb) * 100) : 0;

        const textElem = document.getElementById('ramTextUsage');
        if (textElem) textElem.innerText = `${usedGb} / ${totalGb} GB`;

        const barElem = document.getElementById('ramUsageBar');
        if (barElem) {
            barElem.style.width = `${Math.min(100, percent)}%`;
            if (percent > 85) {
                barElem.style.background = '#ef4444';
            } else if (percent > 70) {
                barElem.style.background = '#f59e0b';
            } else {
                barElem.style.background = '#38bdf8';
            }
        }

        const availElem = document.getElementById('ramAvailableText');
        if (availElem) availElem.innerText = `Available: ${data.available_mem_mb} MB`;

        const percentElem = document.getElementById('ramPercentText');
        if (percentElem) percentElem.innerText = `${percent}% used`;

        // 2. Active Desktop Containers vs Max Limit
        const runningElem = document.getElementById('runningContainersCount');
        if (runningElem) runningElem.innerText = data.running_containers;

        const maxElem = document.getElementById('maxContainersLimit');
        if (maxElem) maxElem.innerText = data.max_concurrent_sessions;

        const slotElem = document.getElementById('containerSlotStatus');
        if (slotElem) {
            const slots = data.max_concurrent_sessions - data.running_containers;
            if (slots > 0) {
                slotElem.innerText = `${slots} slot${slots === 1 ? '' : 's'} available`;
                slotElem.style.color = '#34d399';
            } else {
                slotElem.innerText = `Capacity reached (${data.running_containers}/${data.max_concurrent_sessions})`;
                slotElem.style.color = '#f87171';
            }
        }

        // 3. Max Concurrent Sessions Input
        const inputMax = document.getElementById('inputMaxSessions');
        if (inputMax && document.activeElement !== inputMax) {
            inputMax.value = data.max_concurrent_sessions;
        }

        const hintElem = document.getElementById('recommendedMaxHint');
        if (hintElem) {
            hintElem.innerHTML = `Recommended max for this server: <strong>${data.recommended_max}</strong>`;
        }

        // 4. Status Badge
        const badgeElem = document.getElementById('resourceStatusBadge');
        if (badgeElem) {
            if (!data.can_start) {
                badgeElem.className = 'status-pill status-terminated';
                badgeElem.innerText = data.running_containers >= data.max_concurrent_sessions ? 'At Capacity' : 'Low Memory';
            } else {
                badgeElem.className = 'status-pill status-active';
                badgeElem.innerText = 'Optimal';
            }
        }
    } catch (err) {
        console.error('Failed to load system resources:', err);
    }
}

async function saveMaxSessionsLimit() {
    const input = document.getElementById('inputMaxSessions');
    if (!input) return;
    const limit = parseInt(input.value, 10);
    if (isNaN(limit) || limit < 1) {
        alert('Max concurrent sessions must be at least 1');
        return;
    }

    try {
        const res = await fetch('/api/admin/resources', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_concurrent_sessions: limit }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to update concurrency limit');
        }
        showToast(`Concurrency limit updated to ${limit}`);
        await loadSystemResources();
    } catch (err) {
        alert(`Error saving limit: ${err.message}`);
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
        items.forEach((item, idx) => {
            const sid = item.session_id || '';
            const tok = item.candidate_token || '';
            const status = (item.status || 'unknown').toLowerCase();
            const isRunning = !!item.container_running;
            const fullLink = item.url ? (item.url.startsWith('http') ? item.url : `${window.location.origin}${item.url}`) : '';

            // Status Pill (Pure CSS, NO emojis)
            let statusClass = 'status-ended';
            if (status === 'active') {
                statusClass = 'status-active';
            } else if (status === 'pending') {
                statusClass = 'status-pending';
            } else if (status === 'expired') {
                statusClass = 'status-expired';
            }
            const statusPill = `<span class="status-pill ${statusClass}"><span class="status-dot"></span>${escapeHtml(status.toUpperCase())}</span>`;

            // Container State (Pure CSS, NO emojis)
            let containerBadge = '<span class="container-badge container-na"><span class="container-dot"></span>N/A</span>';
            if (sid) {
                if (isRunning) {
                    containerBadge = '<span class="container-badge container-running"><span class="container-dot"></span>Running</span>';
                } else {
                    containerBadge = '<span class="container-badge container-stopped"><span class="container-dot"></span>Stopped</span>';
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

            // Sleek Actions Dropdown Menu (No Emojis)
            const menuId = `menu_${idx}`;
            let actionsHtml = `
                <div class="table-action-menu" id="${menuId}">
                    <button class="btn-action-dropdown" onclick="toggleTableRowMenu(event, '${menuId}')">
                        Actions ▾
                    </button>
                    <div class="action-dropdown-list">
            `;

            if (status === 'active' && sid) {
                actionsHtml += `
                    <button class="action-dropdown-item" onclick="closeAllActionMenus(); openObserveView('${sid}', '${tok}', '${escapeHtml(item.name || '')}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        Observe Live
                    </button>
                    <button class="action-dropdown-item" onclick="closeAllActionMenus(); openReviewModal('${sid}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                        Review & Replay
                    </button>
                `;
                if (fullLink) {
                    actionsHtml += `
                        <button class="action-dropdown-item" onclick="closeAllActionMenus(); copyToClipboard('${fullLink}', 'Candidate link copied!')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            Copy Candidate Link
                        </button>
                    `;
                }
                actionsHtml += `
                    <div class="action-dropdown-divider"></div>
                    <button class="action-dropdown-item danger" onclick="closeAllActionMenus(); resetSessionPrompt('${sid}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
                        Reset Exam
                    </button>
                    <button class="action-dropdown-item danger" onclick="closeAllActionMenus(); endSessionPrompt('${sid}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/></svg>
                        End & Grade
                    </button>
                `;
            } else if (status === 'pending') {
                if (fullLink) {
                    actionsHtml += `
                        <button class="action-dropdown-item" onclick="closeAllActionMenus(); copyToClipboard('${fullLink}', 'Candidate link copied!')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            Copy Invite Link
                        </button>
                        <a class="action-dropdown-item" href="${fullLink}" target="_blank" onclick="closeAllActionMenus()" style="text-decoration:none;">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                            Open Candidate View
                        </a>
                        <div class="action-dropdown-divider"></div>
                    `;
                }
                actionsHtml += `
                    <button class="action-dropdown-item danger" onclick="closeAllActionMenus(); terminateSessionPrompt('${tok || sid}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        Cancel Invite
                    </button>
                `;
            } else {
                // Ended / Expired / Replaced
                if (sid) {
                    actionsHtml += `
                        <button class="action-dropdown-item" onclick="closeAllActionMenus(); openReviewModal('${sid}')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polygon points="5 3 19 12 5 21 5 3"/></svg>
                            Review & Replay
                        </button>
                    `;
                }
                if (fullLink) {
                    actionsHtml += `
                        <button class="action-dropdown-item" onclick="closeAllActionMenus(); copyToClipboard('${fullLink}', 'Candidate link copied!')">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                            Copy Link
                        </button>
                    `;
                }
                actionsHtml += `
                    <div class="action-dropdown-divider"></div>
                    <button class="action-dropdown-item danger" onclick="closeAllActionMenus(); terminateSessionPrompt('${sid || tok}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:14px;height:14px;"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        Delete Record
                    </button>
                `;
            }

            actionsHtml += `
                    </div>
                </div>
            `;

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
    if (!confirm(`Are you sure you want to terminate or delete session/invite: ${identifier}?`)) {
        return;
    }
    try {
        const res = await fetch(`/api/admin/sessions/${encodeURIComponent(identifier)}/terminate`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        showToast(`Record ${identifier} removed`);
        await loadAdminSessions();
    } catch (err) {
        alert(`Failed to terminate: ${err.message}`);
    }
}

async function loadAdminInfrastructure() {
    const tbody = document.getElementById('adminInfraTableBody');
    const nodesGrid = document.getElementById('fleetNodesGrid');
    if (!tbody) return;

    try {
        const res = await fetch('/api/admin/infrastructure');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        // 1. Render Nodes Cards
        if (nodesGrid && data.nodes) {
            nodesGrid.innerHTML = data.nodes.map(n => `
                <div style="background: #0b111a; border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-weight: 700; font-size: 0.95rem; color: #f8fafc;">${escapeHtml(n.name)}</span>
                        <span class="status-pill status-active" style="font-size: 0.65rem;">${escapeHtml(n.status)}</span>
                    </div>
                    <div style="font-size: 0.78rem; color: #94a3b8; font-family: var(--font-code);">${escapeHtml(n.ip)}</div>
                    <div style="font-size: 0.72rem; color: #64748b; margin-top: 4px;">${escapeHtml(n.role)}</div>
                </div>
            `).join('');
        }

        // 2. Render Resources Table
        if (!data.resources || data.resources.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; color: #64748b; padding: 24px;">
                        No active containers or Incus instances running in the fleet.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = data.resources.map(r => {
            const isDocker = r.kind === 'docker';
            const kindBadge = isDocker 
                ? `<span style="background: #0284c7; color: #fff; padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700;">DOCKER</span>`
                : `<span style="background: #9333ea; color: #fff; padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700;">INCUS</span>`;

            const isRunning = (r.status || '').toLowerCase().includes('running') || (r.status || '').toLowerCase().includes('up');
            const statusBadge = isRunning 
                ? `<span class="status-pill status-active">${escapeHtml(r.status)}</span>`
                : `<span class="status-pill" style="background: #334155; color: #cbd5e1;">${escapeHtml(r.status)}</span>`;

            const sidBadge = r.session_id && r.session_id !== '-'
                ? `<span class="code-cell" style="color: #38bdf8;">${escapeHtml(r.session_id.slice(0, 14))}...</span>`
                : `<span style="color: #64748b;">-</span>`;

            const limits = (r.cpu_limit && r.cpu_limit !== '-') 
                ? `${r.cpu_limit} vCPU, ${r.mem_limit || '-'}`
                : `<span style="color: #64748b;">Host Default</span>`;

            return `
                <tr>
                    <td><strong>${escapeHtml(r.name)}</strong></td>
                    <td style="font-family: var(--font-code); font-size: 0.82rem;">${escapeHtml(r.node)}</td>
                    <td>${kindBadge}</td>
                    <td>${sidBadge}</td>
                    <td style="font-family: var(--font-code); font-size: 0.84rem;">${escapeHtml(r.ip || '-')}</td>
                    <td style="font-size: 0.8rem; color: #cbd5e1;">${limits}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-terminate btn-sm" onclick="terminateResourcePrompt('${r.kind}', '${r.node}', '${r.name}')" title="Terminate container/instance">
                            Terminate
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

    } catch (err) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; color: #ef4444; padding: 20px;">
                    Error loading infrastructure: ${escapeHtml(err.message)}
                </td>
            </tr>
        `;
    }
}

async function terminateResourcePrompt(kind, node, name) {
    if (!name) return;
    if (!confirm(`Are you sure you want to forcibly terminate ${kind} instance '${name}' on node '${node}'?`)) {
        return;
    }
    try {
        const res = await fetch('/api/admin/infrastructure/terminate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kind, node, name })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Termination failed');
        showToast(data.message || `Terminated ${name}`);
        loadAdminInfrastructure();
    } catch (err) {
        alert('Failed to terminate: ' + err.message);
    }
}


window.toggleTableRowMenu = function (e, menuId) {
    e.stopPropagation();
    const menuEl = document.getElementById(menuId);
    if (!menuEl) return;
    const list = menuEl.querySelector('.action-dropdown-list');
    if (!list) return;
    const wasOpen = list.classList.contains('show');
    closeAllActionMenus();
    if (!wasOpen) {
        list.classList.add('show');
    }
};

window.closeAllActionMenus = function () {
    document.querySelectorAll('.action-dropdown-list.show').forEach(el => el.classList.remove('show'));
};

document.addEventListener('click', () => closeAllActionMenus());

async function resetSessionPrompt(sessionId) {
    if (!sessionId) return;
    if (!confirm(`Reset exam for session #${sessionId}?\n\nThis will clear the active exam and reset cluster namespaces.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/admin/sessions/${encodeURIComponent(sessionId)}/reset`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        showToast(`Session ${sessionId} reset and cluster cleaned`);
        await loadAdminSessions();
    } catch (err) {
        alert(`Failed to reset exam: ${err.message}`);
    }
}

async function endSessionPrompt(sessionId) {
    if (!sessionId) return;
    if (!confirm(`End and evaluate session #${sessionId} now?\n\nThis will evaluate candidate tasks and archive the session.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/admin/sessions/${encodeURIComponent(sessionId)}/end`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        showToast(`Session ${sessionId} ended and evaluated`);
        if (data.scorecard) {
            renderAdminScorecard(data.scorecard);
        }
        await loadAdminSessions();
    } catch (err) {
        alert(`Failed to end exam: ${err.message}`);
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
                        <span>${isFlagged ? '<span style="color:#f59e0b;font-weight:700;margin-right:4px;">[FLAG]</span>' : ''}${q.points}pts</span>
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

/* ==========================================================================
   Observe Mode Action Controls (Review & Replay, Reset Exam, End Exam)
   ========================================================================== */

function observeReviewAndReplay() {
    if (!currentObserveSessionId) {
        showToast('No active observe session');
        return;
    }
    openReviewModal(currentObserveSessionId);
}

async function observeResetExam() {
    if (!currentObserveSessionId) return;
    if (!confirm(`Reset exam for session #${currentObserveSessionId}?\n\nThis will clear the session and reset cluster namespaces.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/admin/sessions/${encodeURIComponent(currentObserveSessionId)}/reset`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        showToast(`Session ${currentObserveSessionId} reset and cluster cleaned`);
        await refreshObserveData(currentObserveSessionId);
        await loadAdminSessions();
    } catch (err) {
        alert(`Failed to reset exam: ${err.message}`);
    }
}

async function observeEndExam() {
    if (!currentObserveSessionId) return;
    if (!confirm(`End and evaluate exam for session #${currentObserveSessionId} now?\n\nThis will submit all candidate tasks and grade the exam.`)) {
        return;
    }
    try {
        const res = await fetch(`/api/admin/sessions/${encodeURIComponent(currentObserveSessionId)}/end`, {
            method: 'POST',
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        showToast(`Session ${currentObserveSessionId} ended and evaluated`);
        if (data.scorecard) {
            renderAdminScorecard(data.scorecard);
        }
        await loadAdminSessions();
    } catch (err) {
        alert(`Failed to end exam: ${err.message}`);
    }
}

/* ==========================================================================
   Modals & Scorecard Viewer
   ========================================================================== */

window.openModal = function (modalId) {
    const m = document.getElementById(modalId);
    if (m) m.style.display = 'flex';
};

window.closeModal = function (modalId) {
    const m = document.getElementById(modalId);
    if (m) m.style.display = 'none';
};

function renderAdminScorecard(scorecard) {
    const content = document.getElementById('scorecardModalContent');
    if (!content) return;

    const passed = !!scorecard.passed;
    const score = scorecard.score ?? 0;
    const maxScore = scorecard.max_score ?? 100;
    const pct = scorecard.percentage !== undefined ? scorecard.percentage : Math.round((score / Math.max(1, maxScore)) * 100);

    let tasksHtml = '';
    const results = scorecard.task_results || scorecard.results || [];
    if (results.length > 0) {
        tasksHtml = `
            <table class="admin-table" style="margin-top: 16px;">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Task Title</th>
                        <th>Score</th>
                        <th>Result</th>
                        <th>Feedback</th>
                    </tr>
                </thead>
                <tbody>
                    ${results.map((t, idx) => `
                        <tr>
                            <td>#${t.task_num || (idx + 1)}</td>
                            <td><strong>${escapeHtml(t.title || 'Task')}</strong></td>
                            <td>${t.score !== undefined ? `${t.score}/${t.max_score || t.points || 0}` : '—'}</td>
                            <td>
                                <span class="status-pill ${t.passed ? 'status-active' : 'status-terminated'}">
                                    ${t.passed ? 'PASSED' : 'FAILED'}
                                </span>
                            </td>
                            <td style="font-size: 0.8rem; color: #94a3b8;">${escapeHtml(t.message || '—')}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    content.innerHTML = `
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="margin-bottom: 12px;">
                <span class="status-pill ${passed ? 'status-active' : 'status-terminated'}" style="font-size: 0.95rem; padding: 6px 16px;">
                    <span class="status-dot" style="width: 8px; height: 8px;"></span>
                    ${passed ? 'EXAM PASSED' : 'EXAM FAILED'}
                </span>
            </div>
            <h3 style="font-size: 1.35rem; margin-bottom: 6px; color: ${passed ? '#34d399' : '#f87171'};">
                Final Score: ${pct}%
            </h3>
            <div style="font-size: 0.9rem; color: #94a3b8;">
                Points: <strong>${score}</strong> / ${maxScore} | Exam: ${escapeHtml(scorecard.name || 'Exam Drill')}
            </div>
        </div>
        ${tasksHtml}
    `;

    openModal('modalScorecard');
}

/* ==========================================================================
   Candidate Session Post-Exam Review & Replay Player Engine
   ========================================================================== */

let replayTerm = null;
let replayFitAddon = null;
let replayFrames = [];
let replayDuration = 0;
let replayCurrentTime = 0;
let replayIsPlaying = false;
let replaySpeed = 1.0;
let replayAnimFrameId = null;
let replayLastFrameTime = null;
let replayNextEventIndex = 0;
let replayActiveSessionData = null;
let replayCurrentTab = 'timeline';

window.openReviewModal = async function (sessionId) {
    openModal('modalReview');
    initReplayTerminal();

    const titleEl = document.getElementById('reviewModalTitle');
    const subEl = document.getElementById('reviewModalSubtitle');
    const btnCast = document.getElementById('btnDownloadCast');
    const btnEvents = document.getElementById('btnDownloadEvents');

    titleEl.innerText = `Candidate Session Review: ${sessionId}`;
    subEl.innerText = 'Loading session metadata, timeline, and terminal cast...';

    btnCast.href = `/api/recordings/${sessionId}/cast`;
    btnCast.download = `${sessionId}.cast`;
    btnCast.style.display = 'inline-flex';

    btnEvents.href = `/api/recordings/${sessionId}/events`;
    btnEvents.download = `${sessionId}.events.json`;
    btnEvents.style.display = 'inline-flex';

    pauseReplay();

    try {
        const [detailRes, castRes] = await Promise.all([
            fetch(`/api/recordings/${sessionId}`),
            fetch(`/api/recordings/${sessionId}/cast`)
        ]);

        if (!detailRes.ok) throw new Error('Could not fetch session metadata');
        const sessionData = await detailRes.json();
        replayActiveSessionData = sessionData;

        const dur = sessionData.duration_formatted || (sessionData.duration_seconds ? formatDurationSeconds(sessionData.duration_seconds) : '--:--');
        const scoreStr = sessionData.percentage !== null && sessionData.percentage !== undefined ? `${sessionData.percentage}%` : 'In Progress';
        const stText = sessionData.passed === true ? 'PASSED' : (sessionData.passed === false ? 'FAILED' : 'IN PROGRESS');
        subEl.innerText = `Exam: ${sessionData.name || 'Exam'} | Result: ${stText} (${scoreStr}) | Duration: ${dur} | Total Events: ${sessionData.events_count || 0}`;

        renderReviewSidebar();

        if (castRes.ok) {
            const castText = await castRes.text();
            parseCastRecording(castText);
        } else {
            replayFrames = [];
            replayDuration = sessionData.duration_seconds || 60;
        }

        seekReplay(0);
    } catch (e) {
        subEl.innerText = `Error loading session: ${e.message}`;
    }
};

window.closeReviewModal = function () {
    pauseReplay();
    closeModal('modalReview');
};

function initReplayTerminal() {
    if (replayTerm) {
        replayTerm.reset();
        if (replayFitAddon) {
            setTimeout(() => replayFitAddon.fit(), 50);
        }
        return;
    }
    const container = document.getElementById('replayTerminalContainer');
    if (!container || !window.Terminal) return;

    replayTerm = new Terminal({
        cursorBlink: false,
        fontFamily: "'Fira Code', monospace",
        fontSize: 13,
        lineHeight: 1.2,
        theme: {
            background: '#090d14',
            foreground: '#f1f5f9',
            cursor: '#38bdf8',
            selectionBackground: '#334155',
            black: '#000000',
            red: '#ef4444',
            green: '#10b981',
            yellow: '#f59e0b',
            blue: '#3b82f6',
            magenta: '#a855f7',
            cyan: '#06b6d4',
            white: '#f1f5f9',
        }
    });

    if (window.FitAddon && window.FitAddon.FitAddon) {
        replayFitAddon = new FitAddon.FitAddon();
        replayTerm.loadAddon(replayFitAddon);
    }

    replayTerm.open(container);
    setTimeout(() => {
        if (replayFitAddon) replayFitAddon.fit();
    }, 100);
}

function parseCastRecording(castText) {
    const lines = castText.split('\n');
    replayFrames = [];
    replayDuration = 0;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line || line.startsWith('{')) continue;
        try {
            const entry = JSON.parse(line);
            if (Array.isArray(entry) && entry.length >= 3) {
                const relTime = entry[0];
                const type = entry[1];
                const content = entry[2];
                replayFrames.push({ time: relTime, type, content });
                if (relTime > replayDuration) {
                    replayDuration = relTime;
                }
            }
        } catch (_) {}
    }

    if (replayDuration <= 0 && replayActiveSessionData && replayActiveSessionData.duration_seconds) {
        replayDuration = replayActiveSessionData.duration_seconds;
    }

    const scrubber = document.getElementById('replayScrubber');
    if (scrubber) scrubber.max = Math.max(1, replayDuration);
}

function renderReviewSidebar() {
    const container = document.getElementById('reviewSidebarContent');
    const countEl = document.getElementById('reviewEventCount');
    if (!container || !replayActiveSessionData) return;

    if (replayCurrentTab === 'timeline') {
        const events = replayActiveSessionData.events || [];
        if (countEl) countEl.innerText = `${events.length} events`;

        if (events.length === 0) {
            container.innerHTML = '<div style="padding: 16px; color: #64748b; font-size: 0.82rem; text-align: center;">No structured event logs recorded for this session.</div>';
            return;
        }

        container.innerHTML = `
            <div class="timeline-list">
                ${events.map((ev, idx) => {
                    const t = ev.relative_time !== undefined ? ev.relative_time : 0;
                    const actorBadge = ev.actor === 'admin' ? '<span style="font-size:0.65rem; background:rgba(239,68,68,0.2); color:#fca5a5; padding:1px 4px; border-radius:3px;">ADMIN</span>' : '';
                    let badgeClass = 'badge-info';
                    if (ev.type.includes('START') || ev.type.includes('CONNECT')) badgeClass = 'badge-success';
                    else if (ev.type.includes('END') || ev.type.includes('FAIL') || ev.type.includes('DISCONNECT') || ev.type.includes('SUBMIT')) badgeClass = 'badge-danger';
                    else if (ev.type.includes('FLAG') || ev.type.includes('WARNING')) badgeClass = 'badge-warning';

                    return `
                        <div class="timeline-item" onclick="seekReplay(${t})" data-event-idx="${idx}">
                            <div class="timeline-meta">
                                <span class="timeline-time">${formatReplayTime(t)}</span>
                                <div>
                                    ${actorBadge}
                                    <span class="timeline-badge ${badgeClass}">${escapeHtml(ev.type)}</span>
                                </div>
                            </div>
                            <div style="font-size: 0.78rem; color: #cbd5e1; word-break: break-word;">
                                ${escapeHtml(JSON.stringify(ev.data || {}))}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    } else {
        const tasks = replayActiveSessionData.task_timeline || [];
        if (countEl) countEl.innerText = `${tasks.length} tasks`;

        if (tasks.length === 0) {
            container.innerHTML = '<div style="padding: 16px; color: #64748b; font-size: 0.82rem; text-align: center;">No task transitions recorded.</div>';
            return;
        }

        container.innerHTML = `
            <div class="timeline-list">
                ${tasks.map(task => {
                    const t = task.start_time || 0;
                    return `
                        <div class="timeline-item" onclick="seekReplay(${t})">
                            <div class="timeline-meta">
                                <span class="timeline-time">${formatReplayTime(t)}</span>
                                <span class="timeline-badge badge-primary">Task ${task.task_num}</span>
                            </div>
                            <div style="font-size: 0.82rem; font-weight: 600; color: #f1f5f9; margin-top: 2px;">
                                ${escapeHtml(task.title || 'Task Details')}
                            </div>
                            <div style="font-size: 0.74rem; color: #94a3b8; display: flex; justify-content: space-between; margin-top: 4px;">
                                <span>Duration: ${task.duration ? formatDurationSeconds(task.duration) : '--:--'}</span>
                                <span style="color: ${task.score > 0 ? '#34d399' : '#94a3b8'};">Score: ${task.score !== undefined ? `${task.score}/${task.points}` : '—'}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }
}

window.switchReviewTab = function (tab) {
    replayCurrentTab = tab;
    const btnTimeline = document.getElementById('btnTabTimeline');
    const btnTasks = document.getElementById('btnTabTasks');
    if (tab === 'timeline') {
        if (btnTimeline) btnTimeline.classList.add('active');
        if (btnTasks) btnTasks.classList.remove('active');
    } else {
        if (btnTasks) btnTasks.classList.add('active');
        if (btnTimeline) btnTimeline.classList.remove('active');
    }
    renderReviewSidebar();
};

window.toggleReplayPlayPause = function () {
    if (replayIsPlaying) {
        pauseReplay();
    } else {
        playReplay();
    }
};

function playReplay() {
    if (replayCurrentTime >= replayDuration) {
        seekReplay(0);
    }
    replayIsPlaying = true;
    replayLastFrameTime = performance.now();
    const icon = document.getElementById('replayPlayIcon');
    if (icon) icon.innerText = 'Pause';
    const btn = document.getElementById('btnReplayPlayPause');
    if (btn) btn.classList.remove('primary');
    replayTick();
}

function pauseReplay() {
    replayIsPlaying = false;
    if (replayAnimFrameId) {
        cancelAnimationFrame(replayAnimFrameId);
        replayAnimFrameId = null;
    }
    const icon = document.getElementById('replayPlayIcon');
    if (icon) icon.innerText = 'Play';
    const btn = document.getElementById('btnReplayPlayPause');
    if (btn) btn.classList.add('primary');
}

function replayTick() {
    if (!replayIsPlaying) return;

    const now = performance.now();
    const deltaSeconds = ((now - replayLastFrameTime) / 1000) * replaySpeed;
    replayLastFrameTime = now;

    const newTime = replayCurrentTime + deltaSeconds;
    renderReplayTo(newTime);

    if (newTime >= replayDuration) {
        pauseReplay();
        return;
    }

    replayAnimFrameId = requestAnimationFrame(replayTick);
}

function renderReplayTo(targetTime) {
    targetTime = Math.max(0, Math.min(targetTime, replayDuration));
    while (replayNextEventIndex < replayFrames.length && replayFrames[replayNextEventIndex].time <= targetTime) {
        const frame = replayFrames[replayNextEventIndex];
        if (frame.type === 'o' && replayTerm) {
            replayTerm.write(frame.content);
        }
        replayNextEventIndex++;
    }

    replayCurrentTime = targetTime;
    const scrubber = document.getElementById('replayScrubber');
    if (scrubber) scrubber.value = targetTime;

    const timeDisplay = document.getElementById('replayTimeDisplay');
    if (timeDisplay) {
        timeDisplay.innerText = `${formatReplayTime(targetTime)} / ${formatReplayTime(replayDuration)}`;
    }
}

window.seekReplay = function (targetTime) {
    targetTime = Math.max(0, Math.min(targetTime, replayDuration));
    if (replayTerm) replayTerm.reset();
    replayNextEventIndex = 0;
    replayCurrentTime = 0;
    renderReplayTo(targetTime);
};

window.seekReplayRelative = function (delta) {
    seekReplay(replayCurrentTime + delta);
};

window.restartReplay = function () {
    seekReplay(0);
};

window.setReplaySpeed = function (speed) {
    replaySpeed = parseFloat(speed) || 1.0;
};

window.onScrubberInput = function (val) {
    const time = parseFloat(val);
    pauseReplay();
    seekReplay(time);
};

window.onScrubberChange = function (val) {
    const time = parseFloat(val);
    seekReplay(time);
};

function formatDurationSeconds(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}m ${s}s`;
}

function formatReplayTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
