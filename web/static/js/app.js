/**
 * Kubernetes Exam Web Simulator - Frontend Application Controller
 */

let currentSession = null;
let currentSelectedPreset = null;
let timerInterval = null;
let timerSyncInterval = null;
let targetEndTimestamp = null;
let timeRemainingSeconds = null;
let currentTab = 'desktop';
let isAdminUser = false;
let lastKnownHostClipboard = '';
let lastKnownVncClipboard = '';
let isSyncingClipboard = false;
let pendingHostClipboardText = null;
let clipboardToastTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    initSplitPane();
    initMarked();
    initShortcuts();
    initBeforeUnload();
    loadSession();

    // Close workspace actions dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const dd = document.getElementById('workspaceDropdown');
        if (dd && !dd.contains(e.target)) {
            dd.classList.remove('open');
        }
    });

    // Re-sync timer and desktop clipboard when candidate tab becomes visible or focused
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            fetchServerTimer();
            syncFromVncClipboard(false);
        }
    });
    window.addEventListener('focus', () => {
        fetchServerTimer();
        syncFromVncClipboard(false);
    });

    // Background poll for desktop clipboard changes (every 2.5s when tab is active)
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            syncFromVncClipboard(false);
        }
    }, 2500);

    // Flush any pending desktop clipboard writes whenever the candidate interacts with the page
    // (A genuine user gesture guarantees browser permission for navigator.clipboard.writeText)
    ['click', 'pointerdown', 'keydown'].forEach((evt) => {
        document.addEventListener(evt, () => {
            if (pendingHostClipboardText && navigator.clipboard && navigator.clipboard.writeText) {
                const textToFlush = pendingHostClipboardText;
                pendingHostClipboardText = null;
                navigator.clipboard.writeText(textToFlush).catch(() => {});
            }
        }, { capture: true, passive: true });
    });

    // Event Listeners
    document.getElementById('btnNextTask').addEventListener('click', onNextTask);
    document.getElementById('btnPrevTask').addEventListener('click', onPrevTask);
    document.getElementById('btnRetryTask').addEventListener('click', onRetryTask);
    document.getElementById('btnFlagTask').addEventListener('click', onToggleFlag);
    document.getElementById('btnOpenDrawer').addEventListener('click', openQuestionDrawer);
    const startExamBtn = document.getElementById('btnStartExam');
    if (startExamBtn) startExamBtn.addEventListener('click', openStartModal);
    document.getElementById('btnSubmitExam').addEventListener('click', onSubmitExam);

    // Click-to-copy for any inline code snippets (`code`) across question panes
    document.addEventListener('click', (e) => {
        const code = e.target.closest('code');
        if (!code) return;
        // Skip code inside pre blocks (they have their own Copy button header)
        if (code.closest('pre')) return;

        const text = code.innerText.trim();
        if (text) {
            copyInlineCode(code, text);
        }
    });

    // Listen for clipboard messages coming from noVNC desktop (e.g. copying in terminal)
    window.addEventListener('message', (e) => {
        if (e.data && e.data.type === 'VNC_CLIPBOARD' && typeof e.data.text === 'string') {
            handleIncomingVncClipboard(e.data.text, false);
        }
    });

    // When candidate copies anywhere on host, sync text to VNC desktop
    document.addEventListener('copy', () => {
        setTimeout(async () => {
            try {
                if (navigator.clipboard && navigator.clipboard.readText) {
                    const text = await navigator.clipboard.readText();
                    if (text) syncTextToVnc(text);
                }
            } catch (_) {}
        }, 50);
    });
});

/* ==========================================================================
   Split.js Resizable Split Pane
   ========================================================================== */

function initSplitPane() {
    if (window.Split) {
        Split(['#leftPane', '#rightPane'], {
            sizes: [32, 68],
            minSize: [280, 450],
            gutterSize: 6,
            cursor: 'col-resize',
            onDragEnd: function () {
                // Trigger any resize event for embedded canvas
            }
        });
    }
}


/* ==========================================================================
   Marked & Code Block Syntax Highlighting + Copy Button
   ========================================================================== */

function initMarked() {
    if (window.marked && window.hljs) {
        marked.setOptions({
            highlight: function (code, lang) {
                const language = hljs.getLanguage(lang) ? lang : 'plaintext';
                return hljs.highlight(code, { language }).value;
            },
            gfm: true,
            breaks: true,
        });
    }
}

function renderMarkdown(content) {
    const rawHtml = marked.parse(content || '');
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = rawHtml;

    // Enhance inline code elements with title and button role for click-to-copy
    const inlineCodes = tempDiv.querySelectorAll('code:not(pre code)');
    inlineCodes.forEach((code) => {
        code.setAttribute('title', 'Click to copy');
        code.setAttribute('role', 'button');
    });

    // Wrap code blocks with copy header
    const preBlocks = tempDiv.querySelectorAll('pre');
    preBlocks.forEach((pre) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';

        const header = document.createElement('div');
        header.className = 'code-block-header';
        header.innerHTML = `
            <span>COMMAND / MANIFEST</span>
            <button class="code-copy-btn" onclick="copyCode(this)">
                <span>Copy</span>
            </button>
        `;

        const clonePre = pre.cloneNode(true);
        wrapper.appendChild(header);
        wrapper.appendChild(clonePre);

        pre.parentNode.replaceChild(wrapper, pre);
    });

    return tempDiv.innerHTML;
}

// Universal VNC clipboard synchronizer (Web postMessage + X11 server sync)
window.syncTextToVnc = function (text) {
    if (!text) return;

    // 1. Post to noVNC iframe
    const frame = document.getElementById('desktopFrame');
    if (frame && frame.contentWindow) {
        try {
            frame.contentWindow.postMessage({ type: 'SET_CLIPBOARD', text: text }, '*');
        } catch (_) {}
    }

    // 2. Direct fast non-blocking update to server X11 display :1
    fetch('/api/clipboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text })
    }).catch(() => {});
};

window.copyInlineCode = function (el, text) {
    if (!text && el) text = el.innerText.trim();
    if (!text) return;

    // 1. Copy to host clipboard
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(() => fallbackCopyText(text));
    } else {
        fallbackCopyText(text);
    }

    // 2. Sync to VNC desktop
    syncTextToVnc(text);

    // 3. Visual feedback
    if (el) {
        el.classList.remove('code-copied');
        void el.offsetWidth; // force DOM reflow for CSS animation reset
        el.classList.add('code-copied');
        setTimeout(() => {
            el.classList.remove('code-copied');
        }, 1200);
    }
};

function fallbackCopyText(text) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {
        document.execCommand('copy');
    } catch (_) {}
    document.body.removeChild(ta);
}

window.copyCode = function (btn) {
    const wrapper = btn.closest('.code-block-wrapper');
    const codeElem = wrapper ? wrapper.querySelector('pre code') : null;
    const textToCopy = codeElem ? codeElem.innerText : '';

    if (textToCopy) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(textToCopy).catch(() => fallbackCopyText(textToCopy));
        } else {
            fallbackCopyText(textToCopy);
        }
        syncTextToVnc(textToCopy);

        btn.innerHTML = `<span>Copied</span>`;
        btn.classList.add('copied');
        setTimeout(() => {
            btn.innerHTML = `<span>Copy</span>`;
            btn.classList.remove('copied');
        }, 2000);
    }
};

/* ── Bi-directional VNC <-> Host Clipboard Bridge ───────────────────────── */

function escapeClipboardSnippet(str) {
    return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

window.showClipboardSyncToast = function (text, isInteractive = false) {
    let toast = document.getElementById('clipboardSyncToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'clipboardSyncToast';
        toast.className = 'clipboard-sync-toast';
        document.body.appendChild(toast);
    }

    if (isInteractive) {
        const cleanText = text.replace(/[\r\n\t]+/g, ' ').trim();
        const snippet = cleanText.length > 32 ? cleanText.substring(0, 29) + '...' : cleanText;
        toast.innerHTML = `
            <span class="toast-icon">📋</span>
            <span>Desktop: <code>${escapeClipboardSnippet(snippet)}</code></span>
            <span class="toast-btn">Copy to Host</span>
        `;
        toast.onclick = async (e) => {
            e.stopPropagation();
            if (navigator.clipboard && navigator.clipboard.writeText) {
                try {
                    await navigator.clipboard.writeText(text);
                    pendingHostClipboardText = null;
                    toast.innerHTML = `<span class="toast-icon">✓</span> <span>Copied to Host!</span>`;
                    setTimeout(() => toast.classList.remove('show'), 1500);
                } catch (_) {
                    fallbackCopyText(text);
                }
            } else {
                fallbackCopyText(text);
            }
        };
    } else {
        toast.innerHTML = `<span class="toast-icon">📋</span> <span>${escapeClipboardSnippet(text)}</span>`;
        toast.onclick = () => toast.classList.remove('show');
    }

    toast.classList.add('show');
    clearTimeout(clipboardToastTimer);
    clipboardToastTimer = setTimeout(() => {
        toast.classList.remove('show');
    }, 4500);
};

window.handleIncomingVncClipboard = async function (text, explicitUserAction = false) {
    if (!text || typeof text !== 'string') return;
    text = text.trim();
    if (!text) return;

    // Ignore if identical to what host already sent or previously recorded
    if (text === lastKnownVncClipboard && !explicitUserAction) return;
    if (text === lastKnownHostClipboard && !explicitUserAction) return;
    lastKnownVncClipboard = text;

    let wroteSuccessfully = false;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
            await navigator.clipboard.writeText(text);
            wroteSuccessfully = true;
            pendingHostClipboardText = null;
        } catch (_) {
            // Modern browser security blocked background write (no active user gesture)
            pendingHostClipboardText = text;
        }
    } else {
        pendingHostClipboardText = text;
    }

    if (explicitUserAction) {
        if (!wroteSuccessfully) fallbackCopyText(text);
        const cleanText = text.replace(/[\r\n\t]+/g, ' ').trim();
        const snippet = cleanText.length > 32 ? cleanText.substring(0, 29) + '...' : cleanText;
        showClipboardSyncToast(`Copied from Desktop: "${snippet}"`, false);
    } else if (!wroteSuccessfully) {
        // Show interactive toast and prime for flush on next mouse/key click
        showClipboardSyncToast(text, true);
    }
};

window.syncFromVncClipboard = async function (explicitUserAction = false) {
    if (isSyncingClipboard) return;
    isSyncingClipboard = true;
    try {
        const res = await fetch('/api/clipboard');
        if (!res.ok) return;
        const data = await res.json();
        const text = (data.text || '').trim();
        if (!text) {
            if (explicitUserAction) {
                showClipboardSyncToast('Desktop clipboard is empty', false);
            }
            return;
        }
        await handleIncomingVncClipboard(text, explicitUserAction);
    } catch (err) {
        console.warn('Clipboard fetch error:', err);
    } finally {
        isSyncingClipboard = false;
    }
};

window.copyFromDesktopToHost = async function () {
    await syncFromVncClipboard(true);
};

/* ==========================================================================
   API Client & Session State
   ========================================================================== */

async function loadSession() {
    try {
        const query = window.location.search || '';
        const res = await fetch(`/api/session${query}`);
        const data = await res.json();

        isAdminUser = !!data.is_admin;
        initWorkspaceFrames(data.terminal_port, data.novnc_port);

        // Workspace Actions dropdown always visible in header for both admin & candidate
        const wsDropdown = document.getElementById('workspaceDropdown');
        if (wsDropdown) wsDropdown.style.display = 'inline-block';

        if (data.active && data.current_task) {
            currentSession = data;
            updateUIWithSession(data);
            initTimer(data.time_remaining_seconds, data);
            // If candidate rejoins active session without fullscreen, prompt immediately
            if (!isAdminUser && !document.fullscreenElement) {
                showFullscreenWarning();
            }
        } else {
            // Render clean candidate exam start screen with locked or selected preset
            currentSelectedPreset = data.locked_preset || currentSelectedPreset;
            renderStartScreen(currentSelectedPreset, data.is_admin);
        }
    } catch (err) {
        console.error('Failed to load session:', err);
    }
}

function renderStartScreen(lockedPreset, isAdmin) {
    const preset = lockedPreset || currentSelectedPreset || {
        filename: 'mock-01-acme',
        name: 'Mock Exam 01 — ACME Corp Onboarding',
        description: 'Practice exam with 17 tasks covering core workloads, storage, and troubleshooting.',
        task_count: 17,
        time_limit_minutes: 120,
        pass_threshold_percent: 66,
    };
    currentSelectedPreset = preset;

    // Header updates
    document.getElementById('examTitle').innerText = preset.name;
    document.getElementById('btnOpenDrawer').style.display = 'none';
    const wsDropdown = document.getElementById('workspaceDropdown');
    if (wsDropdown) wsDropdown.style.display = 'inline-block';
    document.getElementById('btnFlagTask').style.display = 'none';
    document.getElementById('btnSubmitExam').style.display = 'none';


    let timerVal = 'UNTIMED';
    if (preset.time_limit_minutes) {
        const th = Math.floor(preset.time_limit_minutes / 60);
        const tm = preset.time_limit_minutes % 60;
        timerVal = `${String(th).padStart(2, '0')}:${String(tm).padStart(2, '0')}:00`;
    }
    document.getElementById('timerValue').innerText = timerVal;

    // Hide Task Header & Footer bars during start screen
    const taskHeader = document.querySelector('.task-header-bar');
    const taskFooter = document.querySelector('.task-footer-bar');
    if (taskHeader) taskHeader.style.display = 'none';
    if (taskFooter) taskFooter.style.display = 'none';

    const adminHtml = isAdmin ? `
        <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border-color); text-align: center;">
            <button class="btn btn-secondary" onclick="openStartModal()" style="font-size: 0.8rem;">
                Change preset (Admin)
            </button>
        </div>
    ` : '';

    const timeBadge = preset.time_limit_minutes ? `${preset.time_limit_minutes} minutes` : 'Untimed';

    document.getElementById('taskDescription').innerHTML = `
        <div class="exam-start-hero">
            <div class="hero-badge-row">
                <span class="hero-badge badge-primary">${timeBadge}</span>
                <span class="hero-badge badge-info">${preset.task_count} tasks</span>
                <span class="hero-badge badge-success">Pass score: ${preset.pass_threshold_percent}%</span>
            </div>

            <h1 class="hero-title">${preset.name}</h1>
            <p class="hero-desc">${preset.description}</p>

            <div class="instructions-card">
                <h3>Exam rules and instructions</h3>
                <ul>
                    <li><strong>Cluster execution:</strong> Tasks run on live Kubernetes clusters (k3d-cka and kubeadm-vms).</li>
                    <li><strong>Sequential progression:</strong> Tasks are delivered one at a time.</li>
                    <li><strong>Context and namespace:</strong> Switch cluster context (<code>kubectl config use-context &lt;context&gt;</code>) and namespace as specified in each prompt.</li>
                    <li><strong>Editor:</strong> Use <strong><code>nano</code></strong> for editing files (<code>Ctrl+O</code> to save, <code>Ctrl+X</code> to exit). <code>KUBE_EDITOR</code> defaults to nano.</li>
                    <li><strong>Flag for review:</strong> Use the Flag button to mark questions to revisit from the questions list.</li>
                    <li><strong>Timer:</strong> The timer begins when you click Start exam.</li>
                </ul>
            </div>

            <div class="hero-action-row">
                <button class="btn-hero-start" onclick="startAssignedExam('${preset.filename}')">
                    START EXAM
                </button>
            </div>

            ${adminHtml}
        </div>
    `;
}

async function startAssignedExam(presetFilename) {
    // Must be called synchronously on the user click gesture before any async fetch
    if (!isAdminUser) enterCandidateFullscreen();

    setLoadingState(true, 'Initializing exam', 'Preparing task 1 and configuring cluster environment...');
    try {
        const payload = (presetFilename === 'all') ? { all_questions: true } : { preset: presetFilename };
        const res = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        currentSession = data;
        updateUIWithSession(data);
        initTimer(data.time_remaining_seconds, data);
    } catch (err) {
        alert(`Failed to start exam: ${err.message}`);
    } finally {
        setLoadingState(false);
    }
}

function updateUIWithSession(data) {
    const task = data.current_task;
    if (!task) return;

    // Header
    document.getElementById('examTitle').innerText = data.name || 'Kubernetes Exam Simulator';

    // Show header action buttons once exam is started
    const drawerBtn = document.getElementById('btnOpenDrawer');
    const wsDropdown = document.getElementById('workspaceDropdown');
    const flagBtn = document.getElementById('btnFlagTask');
    const submitBtn = document.getElementById('btnSubmitExam');

    if (drawerBtn) drawerBtn.style.display = 'inline-flex';
    if (wsDropdown) wsDropdown.style.display = 'inline-block';
    if (flagBtn) flagBtn.style.display = 'inline-flex';
    if (submitBtn) submitBtn.style.display = 'inline-flex';


    // Admin-only buttons
    const adminEndBtn = document.getElementById('btnAdminEndExam');
    const adminResetBtn = document.getElementById('btnAdminResetExam');
    if (isAdminUser) {
        if (adminEndBtn) adminEndBtn.style.display = 'inline-flex';
        if (adminResetBtn) adminResetBtn.style.display = 'inline-flex';
    }

    document.getElementById('drawerLabel').innerText = `Questions (${task.task_num}/${data.total_tasks})`;

    // Show Task Header & Footer bars
    const taskHeader = document.querySelector('.task-header-bar');
    const taskFooter = document.querySelector('.task-footer-bar');
    if (taskHeader) taskHeader.style.display = 'block';
    if (taskFooter) taskFooter.style.display = 'flex';

    // Task Badges (Difficulty is hidden)
    document.getElementById('taskNumberBadge').innerText = `Task ${task.task_num}`;

    const diffBadge = document.getElementById('taskDifficultyBadge');
    if (diffBadge) diffBadge.style.display = 'none';

    document.getElementById('taskPointsBadge').innerText = `${task.points} pts`;
    document.getElementById('taskContextBadge').innerText = `context: ${task.target_context || 'k3d-cka'}`;
    document.getElementById('taskNamespaceBadge').innerText = `ns: ${task.namespace}`;

    // Flag indicator
    const flagIndicator = document.getElementById('taskFlagIndicator');
    if (task.is_flagged) {
        flagIndicator.style.display = 'inline-block';
        flagBtn.classList.add('active');
        document.getElementById('flagLabel').innerText = 'Flagged';
    } else {
        flagIndicator.style.display = 'none';
        flagBtn.classList.remove('active');
        document.getElementById('flagLabel').innerText = 'Flag';
    }

    // Task Content
    document.getElementById('taskHeadline').innerText = task.title;
    document.getElementById('taskDescription').innerHTML = renderMarkdown(task.description);

    // Navigation Buttons
    document.getElementById('btnPrevTask').disabled = (task.task_num <= 1);
    document.getElementById('btnNextTask').disabled = (task.task_num >= data.total_tasks);

    // Keep timer in sync with server on every task update
    if (data.time_remaining_seconds !== undefined && data.time_remaining_seconds !== null) {
        syncTimer(data.time_remaining_seconds, data);
    }
    document.getElementById('taskProgressText').innerText = `Task ${task.task_num} of ${data.total_tasks}`;
}

let term = null;
let fitAddon = null;
let termSocket = null;
let termOnDataDisposable = null;
let termOnResizeDisposable = null;

function initTerminal() {
    if (term) return;
    const container = document.getElementById('terminalContainer');
    if (!container || !window.Terminal) return;

    term = new Terminal({
        cursorBlink: true,
        fontFamily: "'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
        fontSize: 14,
        lineHeight: 1.25,
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
            brightBlack: '#475569',
            brightRed: '#f87171',
            brightGreen: '#34d399',
            brightYellow: '#fbbf24',
            brightBlue: '#60a5fa',
            brightMagenta: '#c084fc',
            brightCyan: '#22d3ee',
            brightWhite: '#ffffff',
        }
    });

    if (window.FitAddon && window.FitAddon.FitAddon) {
        fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
    }

    term.open(container);
    if (fitAddon) {
        setTimeout(() => fitAddon.fit(), 100);
    }

    connectTerminalWebSocket();

    window.addEventListener('resize', () => {
        if (fitAddon && currentTab === 'terminal') {
            fitAddon.fit();
            sendResize();
        }
    });

    // Copy on select (like GCP Cloud Shell / Google Cloud Console)
    // Listens on document mouseup to ensure release outside container is also captured
    document.addEventListener('mouseup', (e) => {
        const termContainer = document.getElementById('terminalContainer');
        if (!termContainer || !term) return;

        if (termContainer.contains(e.target) || (term.element && term.element.contains(e.target))) {
            setTimeout(() => {
                if (term && term.hasSelection()) {
                    const selectedText = term.getSelection();
                    if (selectedText && selectedText.length > 0) {
                        copyTextToClipboard(selectedText);
                        showTerminalCopyToast(termContainer);
                    }
                }
            }, 20);
        }
    });

    // Right-click to paste if no text is currently selected
    container.addEventListener('contextmenu', async (e) => {
        if (term && !term.hasSelection()) {
            e.preventDefault();
            try {
                if (navigator.clipboard && navigator.clipboard.readText) {
                    const text = await navigator.clipboard.readText();
                    if (text && termSocket && termSocket.readyState === WebSocket.OPEN) {
                        termSocket.send(text);
                    }
                }
            } catch (_) {}
        }
    });
}

function copyTextToClipboard(text) {
    if (!text) return;
    // 1. Try modern navigator.clipboard API if available in secure context
    if (window.isSecureContext && navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(() => {
            fallbackExecCommandCopy(text);
        });
        return;
    }
    // 2. Fallback using execCommand for HTTP/non-secure contexts
    fallbackExecCommandCopy(text);
}

function fallbackExecCommandCopy(text) {
    try {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "-9999px";
        textArea.style.opacity = "0";
        textArea.setAttribute("readonly", "");
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    } catch (err) {
        console.warn('Clipboard copy error:', err);
    }
}

function showTerminalCopyToast(container) {
    let toast = document.getElementById('terminalCopyToast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'terminalCopyToast';
        toast.style.cssText = 'position: absolute; top: 14px; right: 20px; background: #0284c7; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; pointer-events: none; z-index: 999; transition: opacity 0.15s ease, transform 0.15s ease; opacity: 0; transform: translateY(-4px); box-shadow: 0 4px 12px rgba(0,0,0,0.5);';
        toast.textContent = 'Copied';
        if (getComputedStyle(container).position === 'static') {
            container.style.position = 'relative';
        }
        container.appendChild(toast);
    }
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-4px)';
    }, 1100);
}

function connectTerminalWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/terminal`;

    termSocket = new WebSocket(wsUrl);
    termSocket.binaryType = 'arraybuffer';

    termSocket.onopen = () => {
        if (fitAddon) {
            fitAddon.fit();
            sendResize();
        }
    };

    termSocket.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
            term.write(new Uint8Array(event.data));
        } else {
            term.write(event.data);
        }
    };

    termSocket.onclose = () => {
        term.write('\r\n\x1b[31m[Session closed. Refresh to reconnect]\x1b[0m\r\n');
    };

    termSocket.onerror = (err) => {
        console.error('Terminal WebSocket error:', err);
    };

    // Dispose previous handlers so reconnects don't stack duplicate listeners
    if (termOnDataDisposable) { termOnDataDisposable.dispose(); termOnDataDisposable = null; }
    if (termOnResizeDisposable) { termOnResizeDisposable.dispose(); termOnResizeDisposable = null; }

    termOnDataDisposable = term.onData((data) => {
        if (termSocket && termSocket.readyState === WebSocket.OPEN) {
            termSocket.send(data);
        }
    });

    termOnResizeDisposable = term.onResize(() => {
        sendResize();
    });
}

function sendResize() {
    if (term && termSocket && termSocket.readyState === WebSocket.OPEN) {
        const resizeMsg = JSON.stringify({
            resize: { rows: term.rows, cols: term.cols }
        });
        termSocket.send(resizeMsg);
    }
}

function initWorkspaceFrames(terminalPort, novncPort) {
    initTerminal();
    switchWorkspaceTab('desktop');
}

/* ==========================================================================
   Navigation Actions (Next / Prev / Jump / Flag / Retry / Submit)
   ========================================================================== */

async function onNextTask() {
    setLoadingState(true, 'Grading and advancing', 'Evaluating task and preparing next scenario...');
    try {
        const res = await fetch('/api/action/next', { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        currentSession = data;
        updateUIWithSession(data);
    } catch (err) {
        alert(`Navigation error: ${err.message}`);
    } finally {
        setLoadingState(false);
    }
}

async function onPrevTask() {
    setLoadingState(true, 'Loading previous task', 'Restoring previous task context...');
    try {
        const res = await fetch('/api/action/prev', { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        currentSession = data;
        updateUIWithSession(data);
    } catch (err) {
        alert(`Navigation error: ${err.message}`);
    } finally {
        setLoadingState(false);
    }
}

async function onJumpTask(taskNum) {
    closeModal('modalDrawer');
    setLoadingState(true, `Loading task ${taskNum}`, 'Configuring cluster for selected task...');
    try {
        const res = await fetch('/api/action/jump', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_num: taskNum }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        currentSession = data;
        updateUIWithSession(data);
    } catch (err) {
        alert(`Jump error: ${err.message}`);
    } finally {
        setLoadingState(false);
    }
}

async function onToggleFlag() {
    if (!currentSession || !currentSession.current_task) return;
    try {
        const res = await fetch('/api/action/flag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_num: currentSession.current_task.task_num }),
        });
        const data = await res.json();
        currentSession.current_task.is_flagged = data.is_flagged;
        updateUIWithSession(currentSession);
    } catch (err) {
        console.error('Flag toggle failed:', err);
    }
}

async function onRetryTask() {
    if (!confirm('Reset this task back to its initial problem state? Any changes made to this task will be reset.')) return;
    setLoadingState(true, 'Resetting task', 'Reapplying initial scenario to cluster...');
    try {
        const res = await fetch('/api/action/retry', { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        alert('Task scenario re-initialized cleanly.');
    } catch (err) {
        alert(`Retry error: ${err.message}`);
    } finally {
        setLoadingState(false);
    }
}

async function onSubmitExam(force = false) {
    if (!force && !confirm('Are you ready to submit your exam for evaluation? This will finalize your score across all questions.')) return;
    setLoadingState(true, 'Grading exam', 'Evaluating tasks and compiling results...');
    try {
        stopTimer();
        const res = await fetch('/api/action/submit', { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        const result = await res.json();
        renderScorecard(result);
    } catch (err) {
        alert(`Submission error: ${err.message}`);
    } finally {
        setLoadingState(false);
    }
}

function setLoadingState(loading, title = 'Processing...', desc = 'Please wait while the environment updates.') {
    const overlay = document.getElementById('globalLoadingOverlay');
    const titleEl = document.getElementById('loadingTitle');
    const descEl = document.getElementById('loadingDesc');

    if (titleEl) titleEl.innerText = title;
    if (descEl) descEl.innerText = desc;

    if (overlay) {
        if (loading) {
            overlay.classList.add('active');
        } else {
            overlay.classList.remove('active');
        }
    }

    const btns = [
        'btnNextTask', 'btnPrevTask', 'btnRetryTask', 'btnSubmitExam',
        'btnAdminEndExam', 'btnAdminResetExam', 'btnOpenDrawer', 'btnFlagTask'
    ];
    btns.forEach(id => {
        const el = document.getElementById(id);
        if (el) el.disabled = loading;
    });
}

/* ==========================================================================
   Server-Authoritative Timer Controller (Calculated from Exam Start Time)
   ========================================================================== */

let examEndTimestampSec = null;  // Unix timestamp when exam expires (start_time + limit)
let serverClockSkewMs = 0;       // (server_now * 1000) - client_now
let timerTickInterval = null;
let timerPollInterval = null;

function initTimer(seconds, sessionData) {
    stopTimer();

    if (seconds === null || seconds === undefined) {
        const timerElem = document.getElementById('timerValue');
        if (timerElem) timerElem.innerText = 'UNTIMED';
        return;
    }

    if (sessionData && sessionData.end_timestamp && sessionData.server_timestamp) {
        examEndTimestampSec = sessionData.end_timestamp;
        serverClockSkewMs = (sessionData.server_timestamp * 1000) - Date.now();
    } else {
        // Fallback if timestamps not present in initial call
        examEndTimestampSec = (Date.now() / 1000) + seconds;
        serverClockSkewMs = 0;
    }

    recalcAndDisplay();

    // 1-second display ticker based strictly on start/end timestamp
    timerTickInterval = setInterval(() => {
        if (!examEndTimestampSec) return;
        recalcAndDisplay();

        if (timeRemainingSeconds <= 0) {
            stopTimer();
            alert('Time has expired. Submitting exam for evaluation.');
            onSubmitExam(true);
        }
    }, 1000);

    // Continuous server sync every 3 seconds to ensure lockstep accuracy
    timerPollInterval = setInterval(fetchServerTimer, 3000);
}

function recalcAndDisplay() {
    if (!examEndTimestampSec) return;
    const currentServerTimeMs = Date.now() + serverClockSkewMs;
    const remainingMs = (examEndTimestampSec * 1000) - currentServerTimeMs;
    timeRemainingSeconds = Math.max(0, Math.round(remainingMs / 1000));
    updateTimerDisplay();
}

async function fetchServerTimer() {
    try {
        const res = await fetch('/api/timer');
        if (!res.ok) return;
        const data = await res.json();
        if (!data.active) {
            stopTimer();
            return;
        }
        if (data.end_timestamp && data.server_timestamp) {
            examEndTimestampSec = data.end_timestamp;
            serverClockSkewMs = (data.server_timestamp * 1000) - Date.now();
            recalcAndDisplay();
        } else if (data.time_remaining_seconds !== null && data.time_remaining_seconds !== undefined) {
            timeRemainingSeconds = data.time_remaining_seconds;
            updateTimerDisplay();
        }
    } catch (e) {
        // silent fail on temporary network hiccup
    }
}

function syncTimer(serverSeconds, sessionData) {
    if (sessionData && sessionData.end_timestamp && sessionData.server_timestamp) {
        examEndTimestampSec = sessionData.end_timestamp;
        serverClockSkewMs = (sessionData.server_timestamp * 1000) - Date.now();
        recalcAndDisplay();
    } else if (serverSeconds !== null && serverSeconds !== undefined) {
        timeRemainingSeconds = serverSeconds;
        updateTimerDisplay();
    }
}

function stopTimer() {
    if (timerTickInterval) clearInterval(timerTickInterval);
    if (timerPollInterval) clearInterval(timerPollInterval);
    timerTickInterval = null;
    timerPollInterval = null;
    examEndTimestampSec = null;
    serverClockSkewMs = 0;
    timeRemainingSeconds = null;
}

function updateTimerDisplay() {
    const timerElem = document.getElementById('timerValue');
    const timerCard = document.getElementById('timerCard');

    const h = Math.floor(timeRemainingSeconds / 3600);
    const m = Math.floor((timeRemainingSeconds % 3600) / 60);
    const s = timeRemainingSeconds % 60;

    const formatted = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    timerElem.innerText = formatted;

    // Visual warning thresholds
    if (timeRemainingSeconds < 600) {
        timerCard.className = 'timer-card timer-critical';
    } else if (timeRemainingSeconds < 1800) {
        timerCard.className = 'timer-card timer-warning';
    } else {
        timerCard.className = 'timer-card';
    }
}

/* ==========================================================================
   Question Drawer & Modals
   ========================================================================== */

async function openQuestionDrawer() {
    try {
        const res = await fetch('/api/questions');
        const data = await res.json();
        const grid = document.getElementById('questionDrawerGrid');
        grid.innerHTML = '';

        data.questions.forEach((q) => {
            const card = document.createElement('div');
            let cardClass = 'question-card';
            if (q.is_current) cardClass += ' current-card';
            if (q.is_flagged) cardClass += ' flagged-card';
            card.className = cardClass;

            const flagText = q.is_flagged ? '<span style="color:#f59e0b;font-weight:600;font-size:0.75rem;">FLAGGED</span>' : '';
            
            // Candidate status: Never reveal pass/fail score during the exam
            let statusBadge = '<span style="color:var(--text-dim);font-size:0.75rem;">PENDING</span>';
            if (q.is_current) {
                statusBadge = '<span style="color:var(--accent-yellow);font-weight:700;font-size:0.75rem;">CURRENT</span>';
            } else if (q.is_flagged) {
                statusBadge = '<span style="color:#f59e0b;font-weight:700;font-size:0.75rem;">FLAGGED</span>';
            } else if (q.score_data !== null && q.score_data !== undefined) {
                statusBadge = '<span style="color:var(--accent-blue);font-weight:600;font-size:0.75rem;">ATTEMPTED</span>';
            }

            card.innerHTML = `
                <div class="card-top">
                    <span class="card-num">Task ${q.task_num}</span>
                    ${flagText}
                </div>
                <div class="card-title">${q.title}</div>
                <div class="card-footer">
                    <span>${q.points} pts • context: ${q.target_context}</span>
                    ${statusBadge}
                </div>
            `;

            card.onclick = () => onJumpTask(q.task_num);
            grid.appendChild(card);
        });

        openModal('modalDrawer');
    } catch (err) {
        console.error('Failed to open question drawer:', err);
    }
}

async function openStartModal() {
    try {
        const res = await fetch('/api/presets');
        const data = await res.json();
        const container = document.getElementById('presetListContainer');
        container.innerHTML = '';

        const activeFilename = currentSelectedPreset ? currentSelectedPreset.filename : (data.selected || 'mock-01-acme');

        data.presets.forEach((p) => {
            const card = document.createElement('div');
            const isSelected = (activeFilename === p.filename);
            card.className = `preset-card ${isSelected ? 'preset-selected' : ''}`;

            const taskCount = p.task_count || (p.questions ? p.questions.length : 17);
            const timeLimit = p.time_limit_minutes ? `${p.time_limit_minutes} mins` : 'Untimed';
            const passPct = p.pass_threshold_percent || 66;

            card.innerHTML = `
                <div class="preset-card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div class="preset-title" style="margin-bottom: 0;">${p.name || p.filename}</div>
                    ${isSelected ? '<span class="badge badge-success" style="font-size:0.75rem;padding:2px 8px;border-radius:12px;">Selected</span>' : ''}
                </div>
                <div class="preset-desc">${p.description || 'Practice exam tasks.'}</div>
                <div class="preset-meta" style="margin-top: 8px; font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 12px;">
                    <span>⏱ ${timeLimit}</span>
                    <span>📋 ${taskCount} tasks</span>
                    <span>🎯 Pass: ${passPct}%</span>
                </div>
            `;
            // Selecting only stages the preset; user clicks START EXAM on the start screen to begin
            card.onclick = () => selectPreset(p);
            container.appendChild(card);
        });

        const fullCard = document.getElementById('cardFullCurriculum');
        const fullBadge = document.getElementById('badgeFullCurriculum');
        if (fullCard) {
            if (activeFilename === 'all') {
                fullCard.classList.add('preset-selected');
                if (fullBadge) fullBadge.style.display = 'inline-block';
            } else {
                fullCard.classList.remove('preset-selected');
                if (fullBadge) fullBadge.style.display = 'none';
            }
        }

        openModal('modalStart');
    } catch (err) {
        console.error('Failed to load presets:', err);
    }
}

function selectPreset(p) {
    currentSelectedPreset = {
        filename: p.filename,
        name: p.name || p.filename,
        description: p.description || 'Practice exam tasks.',
        task_count: p.task_count || (p.questions ? p.questions.length : 17),
        time_limit_minutes: p.time_limit_minutes,
        pass_threshold_percent: p.pass_threshold_percent || 66,
    };

    closeModal('modalStart');

    fetch('/api/presets/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset: p.filename }),
    }).catch(err => console.warn('Failed to persist preset on server:', err));

    renderStartScreen(currentSelectedPreset, isAdminUser);
}

function selectFullCurriculum() {
    currentSelectedPreset = {
        filename: 'all',
        name: 'Full Curriculum (All 111 Tasks)',
        description: 'Practice all 111 questions in sequential order.',
        task_count: 111,
        time_limit_minutes: null,
        pass_threshold_percent: 66,
    };

    closeModal('modalStart');

    fetch('/api/presets/select', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset: 'all' }),
    }).catch(err => console.warn('Failed to persist preset on server:', err));

    renderStartScreen(currentSelectedPreset, isAdminUser);
}

function renderScorecard(result) {
    document.getElementById('scorePercentage').innerText = `${result.percentage}%`;
    const statusBadge = document.getElementById('scoreStatusBadge');
    if (result.passed) {
        statusBadge.innerText = 'PASSED';
        statusBadge.className = 'score-status passed';
    } else {
        statusBadge.innerText = 'FAILED';
        statusBadge.className = 'score-status failed';
    }

    document.getElementById('scoreBreakdownText').innerText = `${result.total_earned} / ${result.total_possible} points earned`;

    const tbody = document.getElementById('scorecardTableBody');
    tbody.innerHTML = '';

    result.scorecard.forEach((row) => {
        const tr = document.createElement('tr');
        const statusHtml = row.passed
            ? `<span style="color:var(--accent-green);font-weight:700;">PASS</span>`
            : `<span style="color:var(--accent-red);font-weight:700;">FAIL</span>`;

        tr.innerHTML = `
            <td>${row.task_num}</td>
            <td><code>${row.id}</code></td>
            <td><strong>${row.title}</strong></td>
            <td>${row.domain}</td>
            <td><code>context: ${row.context}</code></td>
            <td><strong>${row.score}/${row.max_score}</strong></td>
            <td>${statusHtml}</td>
            <td style="color:var(--text-muted);font-size:0.8rem;">${row.message}</td>
        `;
        tbody.appendChild(tr);
    });

    openModal('modalScorecard');
}

/* ==========================================================================
   Workspace Tab Switching & Fullscreen
   ========================================================================== */

window.switchWorkspaceTab = function (tab) {
    currentTab = tab;
    const termBtn = document.getElementById('tabTerminal');
    const vncBtn = document.getElementById('tabDesktop');
    const termContainer = document.getElementById('terminalContainer');
    const vncFrame = document.getElementById('desktopFrame');

    if (tab === 'terminal') {
        if (termBtn) termBtn.classList.add('active');
        if (vncBtn) vncBtn.classList.remove('active');
        if (termContainer) termContainer.classList.add('active-frame');
        if (vncFrame) vncFrame.classList.remove('active-frame');
        if (fitAddon) {
            setTimeout(() => {
                fitAddon.fit();
                sendResize();
                if (term) term.focus();
            }, 50);
        }
    } else {
        if (vncBtn) vncBtn.classList.add('active');
        if (termBtn) termBtn.classList.remove('active');
        if (vncFrame) vncFrame.classList.add('active-frame');
        if (termContainer) termContainer.classList.remove('active-frame');
        requestKeyboardLock();

        const host = window.location.hostname || '10.8.0.15';
        const port = (currentSession && currentSession.novnc_port) || '6080';
        const vncUrl = `http://${host}:${port}/vnc.html?autoconnect=true&resize=remote&reconnect=true`;
        if (vncFrame && (!vncFrame.src || vncFrame.src === 'about:blank' || !vncFrame.src.includes(`:${port}/`))) {
            console.log('[VNC] Setting iframe src to:', vncUrl);
            vncFrame.src = vncUrl;
        }
    }
};

window.openDesktopInNewTab = function () {
    const host = window.location.hostname || 'localhost';
    const port = (currentSession && currentSession.novnc_port) || '6080';
    window.open(`http://${host}:${port}/vnc.html?autoconnect=true&resize=remote&reconnect=true`, '_blank');
};

window.toggleWorkspaceDropdown = function (event) {
    if (event) event.stopPropagation();
    const dd = document.getElementById('workspaceDropdown');
    if (dd) dd.classList.toggle('open');
};

window.closeWorkspaceDropdown = function () {
    const dd = document.getElementById('workspaceDropdown');
    if (dd) dd.classList.remove('open');
};


/* ── Admin Controls ─────────────────────────────────────────────────────── */

window.adminEndExam = async function () {
    if (!confirm('End the exam now and show results?\n\nThis cannot be undone.')) return;
    setLoadingState(true, 'Ending exam', 'Evaluating tasks and compiling scorecard...');
    try {
        const res = await fetch('/api/action/submit', { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        renderScorecard(data);
    } catch (err) {
        alert('Failed to end exam: ' + err.message);
    } finally {
        setLoadingState(false);
    }
};

window.adminResetExam = async function () {
    if (!confirm('Reset exam?\n\nThis will clear the current session and return to the start screen.')) return;
    setLoadingState(true, 'Resetting exam', 'Clearing session and resetting cluster namespaces...');
    try {
        const res = await fetch('/api/reset', { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        // Hide admin buttons, reload state
        const adminEndBtn = document.getElementById('btnAdminEndExam');
        const adminResetBtn = document.getElementById('btnAdminResetExam');
        if (adminEndBtn) adminEndBtn.style.display = 'none';
        if (adminResetBtn) adminResetBtn.style.display = 'none';
        currentSession = null;
        if (timerInterval) clearInterval(timerInterval);
        if (timerSyncInterval) clearInterval(timerSyncInterval);
        targetEndTimestamp = null;
        timeRemainingSeconds = null;
        await loadSession();
    } catch (err) {
        alert('Failed to reset exam: ' + err.message);
    } finally {
        setLoadingState(false);
    }
};

window.reloadWorkspaceFrame = function () {
    if (currentTab === 'terminal') {
        if (termSocket) {
            termSocket.close();
        }
        if (term) {
            term.reset();
        }
        connectTerminalWebSocket();
    } else {
        const frame = document.getElementById('desktopFrame');
        if (frame) frame.src = frame.src;
    }
};

/* ── Virtual Key Injection (Esc, Tab, Ctrl+C) ──────────────────── */

window.sendVirtualKey = function (keyType) {
    if (currentTab === 'terminal') {
        if (termSocket && termSocket.readyState === WebSocket.OPEN) {
            if (keyType === 'escape') termSocket.send('\x1b');
            else if (keyType === 'tab') termSocket.send('\t');
            else if (keyType === 'ctrl_c') termSocket.send('\x03');
            if (term) term.focus();
        }
    } else {
        const frame = document.getElementById('desktopFrame');
        if (frame && frame.contentWindow) {
            frame.contentWindow.postMessage({ type: 'SEND_VIRTUAL_KEY', key: keyType }, '*');
        }
    }
};

/* ── Admin Fullscreen Toggle ───────────────────────────────────── */

window.adminToggleFullscreen = function () {
    window.toggleFullscreen();
};

/* ── Keyboard Lock & Fullscreen Enforcement ─────────────────────────────── */

async function requestKeyboardLock() {
    if (navigator.keyboard && navigator.keyboard.lock) {
        try {
            // Lock all keys (Escape, Tab, Alt+Tab, etc.) so vim/nano and terminals receive Escape directly
            await navigator.keyboard.lock();
            console.log('[KeyboardLock] Full keyboard lock enabled (Escape captured for vim)');
        } catch (err) {
            console.warn('[KeyboardLock] Keyboard lock not permitted or unsupported:', err);
        }
    }
}

function releaseKeyboardLock() {
    if (navigator.keyboard && navigator.keyboard.unlock) {
        try {
            navigator.keyboard.unlock();
        } catch (err) {}
    }
}

function enterCandidateFullscreen() {
    const el = document.documentElement;
    if (el.requestFullscreen) {
        el.requestFullscreen().then(requestKeyboardLock).catch(() => {});
    } else if (el.webkitRequestFullscreen) {
        el.webkitRequestFullscreen();
        requestKeyboardLock();
    }
}

function showFullscreenWarning() {
    if (isAdminUser) return;
    if (document.getElementById('fsWarningOverlay')) return;
    const overlay = document.createElement('div');
    overlay.id = 'fsWarningOverlay';
    overlay.style.cssText = [
        'position:fixed', 'inset:0', 'z-index:2147483647',
        'background:rgba(9,13,20,0.96)',
        'backdrop-filter:blur(10px)',
        '-webkit-backdrop-filter:blur(10px)',
        'display:flex', 'flex-direction:column',
        'align-items:center', 'justify-content:center',
        'color:#fff', 'font-family:Inter,sans-serif', 'text-align:center',
        'padding:24px',
        'gap:18px'
    ].join(';');
    overlay.innerHTML = `
        <h2 style="margin:0;font-size:1.6rem;font-weight:800;color:#f87171;letter-spacing:-0.02em;">EXAM LOCKED: FULLSCREEN REQUIRED</h2>
        <p style="margin:0;color:#94a3b8;max-width:460px;font-size:0.95rem;line-height:1.6;">
            Exam policy requires fullscreen mode. Your workspace is locked. Click below to return to fullscreen and resume.
        </p>
        <button id="fsReturnBtn" style="margin-top:8px;padding:14px 40px;border-radius:8px;border:1px solid #38bdf8;background:linear-gradient(135deg,#0284c7,#0369a1);color:#fff;font-size:1.05rem;cursor:pointer;font-weight:700;box-shadow:0 4px 15px rgba(2,132,199,0.4);">
            Return to fullscreen and resume
        </button>
    `;
    document.body.appendChild(overlay);
    document.getElementById('fsReturnBtn').addEventListener('click', () => {
        overlay.remove();
        enterCandidateFullscreen();
    });
}

(function initFullscreenGuard() {
    function onFullscreenChange() {
        const isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement);
        if (isFullscreen) {
            requestKeyboardLock();
            const overlay = document.getElementById('fsWarningOverlay');
            if (overlay) overlay.remove();
        } else {
            releaseKeyboardLock();
            if (!isAdminUser && currentSession) {
                showFullscreenWarning();
            }
        }
    }

    document.addEventListener('fullscreenchange', onFullscreenChange);
    document.addEventListener('webkitfullscreenchange', onFullscreenChange);

    // Prevent context menu (right click inspect) for candidates
    document.addEventListener('contextmenu', (e) => {
        if (!isAdminUser) e.preventDefault();
    });

    // Block F12 / DevTools hotkeys for candidates
    document.addEventListener('keydown', (e) => {
        if (!isAdminUser) {
            if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && ['I', 'i', 'J', 'j', 'C', 'c'].includes(e.key))) {
                e.preventDefault();
            }
        }
    });
}());

window.toggleFullscreen = function () {
    const el = document.documentElement;
    if (!document.fullscreenElement && !document.webkitFullscreenElement) {
        if (el.requestFullscreen) {
            el.requestFullscreen().then(requestKeyboardLock).catch(() => {});
        } else if (el.webkitRequestFullscreen) {
            el.webkitRequestFullscreen();
            requestKeyboardLock();
        }
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen().catch(() => {});
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
    }
};

/* ==========================================================================
   Keyboard Shortcuts & Safety
   ========================================================================== */

function initShortcuts() {
    function handleShortcutKey(key) {
        const k = key.toLowerCase();
        if (k === 'n') {
            onNextTask();
        } else if (k === 'p') {
            onPrevTask();
        } else if (k === 'f') {
            onToggleFlag();
        } else if (k === 'q') {
            openQuestionDrawer();
        }
    }

    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.altKey) {
            const k = e.key.toLowerCase();
            if (['n', 'p', 'f', 'q'].includes(k)) {
                e.preventDefault();
                handleShortcutKey(k);
            }
        }
    });

    // Receive shortcuts bridged from embedded noVNC iframe
    window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'EXAM_SHORTCUT' && event.data.key) {
            handleShortcutKey(event.data.key);
        }
    });
}

function initBeforeUnload() {
    window.addEventListener('beforeunload', (e) => {
        if (currentSession && currentSession.active) {
            e.preventDefault();
            e.returnValue = 'Your active exam session is currently in progress. Are you sure you want to leave?';
        }
    });
}

/* ==========================================================================
   Modal Helpers
   ========================================================================== */

window.openModal = function (modalId) {
    const m = document.getElementById(modalId);
    if (m) m.style.display = 'flex';
};

window.closeModal = function (modalId) {
    const m = document.getElementById(modalId);
    if (m) m.style.display = 'none';
};
