import { getCurrentInstance, onBeforeUnmount, readonly, ref, shallowRef } from 'vue'

import { postClipboardToFrame } from '@/composables/useVnc'

/**
 * useClipboard (FE-027) — bidirectional host <-> VNC desktop clipboard sync.
 *
 * Faithful port of the legacy candidate bridge (`web/static/js/app.js`), per the
 * strict-parity decision D-007:
 *
 *   - `syncTextToVnc`              (`app.js:256`) host    -> desktop
 *   - `handleIncomingVncClipboard` (`app.js:400`) desktop -> host
 *   - `syncFromVncClipboard`       (`app.js:436`) HTTP fallback read
 *   - `copyFromDesktopToHost`      (`app.js:459`) overflow action
 *   - user-gesture flush of `pendingHostClipboardText` (`app.js:120-130`)
 *
 * Transport:
 *   - WS `/ws/session/<sid>`: inbound `{type:'clipboard_update', text}` and
 *     outbound `{type:'clipboard_copy', text}` (server.py:2061/2114, :2235).
 *   - HTTP `GET/POST /api/clipboard` (server.py:562/584) is used only while the
 *     WS is closed, so there is **no busy polling when connected**.
 *
 * The user-gesture workaround is preserved verbatim: a blocked background
 * `navigator.clipboard.writeText` stores the text in `pendingHostClipboardText`
 * and the next `click`/`pointerdown`/`keydown` flushes it from a real gesture.
 * The component (`ClipboardBridge.vue`) owns those DOM listeners; this module
 * exposes `flushPendingHostClipboard()` for it to call.
 */

/** `WebSocket` readyState values, declared locally to avoid a DOM global dep. */
export const SOCKET_CONNECTING = 0
export const SOCKET_OPEN = 1

export const DEFAULT_CLIPBOARD_POLL_INTERVAL_MS = 5000
export const DEFAULT_CLIPBOARD_RECONNECT_DELAY_MS = 3000
export const DEFAULT_COPY_READ_DELAY_MS = 50

/** Structural view of the socket we drive (matches the DOM `WebSocket`). */
export interface ClipboardSocket {
  readyState: number
  send(data: string): void
  close(code?: number, reason?: string): void
  onopen: ((event: unknown) => void) | null
  onmessage: ((event: { data: unknown }) => void) | null
  onclose: ((event: unknown) => void) | null
  onerror: ((event: unknown) => void) | null
}

export interface ClipboardUpdate {
  text: string
}

export interface ClipboardDataResponse {
  text?: string
}

/** Extract a typed `clipboard_update` payload from a raw WS frame, if it is one. */
export function parseClipboardUpdate(raw: unknown): ClipboardUpdate | null {
  if (typeof raw !== 'string') return null
  try {
    const data = JSON.parse(raw) as { type?: unknown; text?: unknown }
    if (!data || data.type !== 'clipboard_update') return null
    if (typeof data.text !== 'string' || data.text.length === 0) return null
    return { text: data.text }
  } catch {
    return null
  }
}

/** Legacy `fallbackCopyText` (`app.js:309`) — `execCommand` copy for insecure contexts. */
export function fallbackCopyText(text: string, doc: Document | undefined): void {
  if (!doc || !text) return
  const area = doc.createElement('textarea')
  area.value = text
  area.style.position = 'fixed'
  area.style.opacity = '0'
  doc.body.appendChild(area)
  area.focus()
  area.select()
  try {
    doc.execCommand('copy')
  } catch {
    /* clipboard may be unavailable; nothing else we can do */
  }
  doc.body.removeChild(area)
}

export interface UseClipboardOptions {
  /** Session id (or getter) used to build the default `/ws/session/<id>` URL. */
  sessionId?: string | (() => string | null | undefined)
  /** Explicit socket URL. Takes precedence over `sessionId`. */
  url?: string | (() => string)
  /** Whether the session is active (getter). Gates the fallback poll/visibility sync. */
  active?: boolean | (() => boolean)
  /** Injectable socket factory (tests). Defaults to the global `WebSocket`. */
  createSocket?: (url: string) => ClipboardSocket
  /** Getter for the noVNC iframe that receives `SET_CLIPBOARD`. */
  frame?: () => HTMLIFrameElement | null | undefined
  /** Override for pushing text into the noVNC iframe (tests). */
  sendToFrame?: (frame: HTMLIFrameElement | null, text: string) => boolean
  /** Injectable clipboard (tests). Defaults to `navigator.clipboard`. */
  clipboard?: () => Clipboard | undefined
  /** Injectable fetch (tests). Defaults to the global `fetch`. */
  fetchImpl?: typeof fetch
  /** Injectable document (tests / SSR). Defaults to the global `document`. */
  document?: () => Document | undefined
  /** Connect immediately on creation. Default `true`. */
  autoConnect?: boolean
  /** Fallback poll interval while the WS is disconnected (ms). Default 5000. */
  pollIntervalMs?: number
  /** Delay before re-opening a closed socket (ms). Default 3000. */
  reconnectDelayMs?: number
  /** Delay before reading the host clipboard after a `copy` event (ms). Default 50. */
  copyReadDelayMs?: number
  /**
   * Called when the desktop clipboard is pulled into the host. `explicit` is
   * `true` for a deliberate user action (overflow "Copy from Desktop").
   */
  onDesktopClipboard?: (text: string, explicitUserAction: boolean) => void
  /** Called when an explicit pull finds the desktop clipboard empty. */
  onEmpty?: () => void
}

function defaultSocketUrl(sessionId: string): string {
  if (typeof window === 'undefined') return `/ws/session/${sessionId}`
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/session/${sessionId}`
}

function defaultCreateSocket(url: string): ClipboardSocket {
  return new WebSocket(url) as unknown as ClipboardSocket
}

export function useClipboard(options: UseClipboardOptions = {}) {
  const connected = ref(false)
  const polling = ref(false)
  const latestDesktopClipboard = ref('')
  const pendingHostClipboardText = ref<string | null>(null)
  const socket = shallowRef<ClipboardSocket | null>(null)

  const pollIntervalMs = options.pollIntervalMs ?? DEFAULT_CLIPBOARD_POLL_INTERVAL_MS
  const reconnectDelayMs = options.reconnectDelayMs ?? DEFAULT_CLIPBOARD_RECONNECT_DELAY_MS
  const copyReadDelayMs = options.copyReadDelayMs ?? DEFAULT_COPY_READ_DELAY_MS
  const factory = options.createSocket ?? defaultCreateSocket

  // Plain (non-reactive) cross-event bookkeeping, mirroring legacy globals.
  let lastKnownHostClipboard = ''
  let lastKnownVncClipboard = ''
  let isSyncingClipboard = false
  let pollHandle: ReturnType<typeof setInterval> | null = null
  let reconnectHandle: ReturnType<typeof setTimeout> | null = null
  let stopped = true

  function resolveClipboard(): Clipboard | undefined {
    if (options.clipboard) return options.clipboard()
    return typeof navigator !== 'undefined' ? navigator.clipboard : undefined
  }

  function resolveDocument(): Document | undefined {
    if (options.document) return options.document()
    return typeof document !== 'undefined' ? document : undefined
  }

  function resolveFetch(): typeof fetch | undefined {
    if (options.fetchImpl) return options.fetchImpl
    return typeof fetch !== 'undefined' ? fetch : undefined
  }

  function resolveFrame(): HTMLIFrameElement | null {
    return options.frame?.() ?? null
  }

  function isActive(): boolean {
    const value = typeof options.active === 'function' ? options.active() : options.active
    return value !== false
  }

  function resolveSessionId(): string {
    const raw = typeof options.sessionId === 'function' ? options.sessionId() : options.sessionId
    const trimmed = typeof raw === 'string' ? raw.trim() : ''
    return trimmed.length > 0 ? trimmed : 'active'
  }

  function resolveUrl(): string {
    if (typeof options.url === 'function') return options.url()
    if (typeof options.url === 'string') return options.url
    return defaultSocketUrl(resolveSessionId())
  }

  /** `POST /api/clipboard` — legacy fast fallback, used only when the WS is down. */
  async function postClipboardToServer(text: string): Promise<void> {
    const doFetch = resolveFetch()
    if (!doFetch) return
    try {
      await doFetch('/api/clipboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      })
    } catch {
      /* non-blocking, fire-and-forget (legacy `.catch(() => {})`) */
    }
  }

  /** `GET /api/clipboard` — returns trimmed text, or `null` when unavailable. */
  async function getClipboardFromServer(): Promise<string | null> {
    const doFetch = resolveFetch()
    if (!doFetch) return null
    try {
      const response = await doFetch('/api/clipboard')
      if (!response.ok) return null
      const data = (await response.json()) as ClipboardDataResponse
      return (data.text ?? '').trim()
    } catch {
      return null
    }
  }

  /** `syncTextToVnc` (`app.js:256`) — host -> desktop (postMessage + WS/HTTP). */
  function sendToVnc(text: string): void {
    if (!text) return
    lastKnownHostClipboard = text.trim()

    const frame = resolveFrame()
    const sendToFrame = options.sendToFrame ?? postClipboardToFrame
    if (frame) sendToFrame(frame, text)

    const sock = socket.value
    if (sock && sock.readyState === SOCKET_OPEN) {
      try {
        sock.send(JSON.stringify({ type: 'clipboard_copy', text }))
        return
      } catch {
        /* fall through to the HTTP fallback */
      }
    }

    void postClipboardToServer(text)
  }

  /** `handleIncomingVncClipboard` (`app.js:400`) — desktop -> host. */
  async function handleVncClipboard(text: string, explicitUserAction = false): Promise<void> {
    if (!text || typeof text !== 'string') return
    const normalized = text.trim()
    if (!normalized) return

    // Ignore if identical to what the host already sent or previously recorded.
    if (normalized === lastKnownVncClipboard && !explicitUserAction) return
    if (normalized === lastKnownHostClipboard && !explicitUserAction) return
    lastKnownVncClipboard = normalized
    latestDesktopClipboard.value = normalized

    let wroteSuccessfully = false
    const clipboard = resolveClipboard()
    if (clipboard?.writeText) {
      try {
        await clipboard.writeText(normalized)
        wroteSuccessfully = true
        pendingHostClipboardText.value = null
      } catch {
        // Modern browser security blocked the background write (no user gesture).
        pendingHostClipboardText.value = normalized
      }
    } else {
      pendingHostClipboardText.value = normalized
    }

    if (explicitUserAction) {
      if (!wroteSuccessfully) fallbackCopyText(normalized, resolveDocument())
      options.onDesktopClipboard?.(normalized, true)
    } else if (!wroteSuccessfully) {
      // Prime for flush on the next mouse/key gesture and notify the host.
      options.onDesktopClipboard?.(normalized, false)
    }
  }

  /** `syncFromVncClipboard` (`app.js:436`) — HTTP read, skipped while WS is connected. */
  async function syncFromVnc(explicitUserAction = false): Promise<void> {
    if (isSyncingClipboard) return
    if (connected.value && !explicitUserAction) return
    isSyncingClipboard = true
    try {
      const text = await getClipboardFromServer()
      if (text === null) return
      if (!text) {
        if (explicitUserAction) options.onEmpty?.()
        return
      }
      await handleVncClipboard(text, explicitUserAction)
    } finally {
      isSyncingClipboard = false
    }
  }

  /** `copyFromDesktopToHost` (`app.js:459`) — the overflow "Copy from Desktop" action. */
  async function copyFromDesktopToHost(): Promise<boolean> {
    let text = (latestDesktopClipboard.value || '').trim()
    if (!text) text = ((await getClipboardFromServer()) ?? '').trim()

    if (!text) {
      options.onEmpty?.()
      return false
    }

    latestDesktopClipboard.value = text
    lastKnownVncClipboard = text
    pendingHostClipboardText.value = null

    let wroteSuccessfully = false
    const clipboard = resolveClipboard()
    if (clipboard?.writeText) {
      try {
        await clipboard.writeText(text)
        wroteSuccessfully = true
      } catch {
        /* fall through to the legacy execCommand fallback */
      }
    }

    if (!wroteSuccessfully) fallbackCopyText(text, resolveDocument())
    options.onDesktopClipboard?.(text, true)
    return true
  }

  /**
   * Flush a clipboard write that was blocked for lack of a user gesture. Must be
   * invoked from a real `click`/`pointerdown`/`keydown` handler (`app.js:120`).
   * Returns `true` when text was pending and a write was attempted.
   */
  function flushPendingHostClipboard(): boolean {
    const text = pendingHostClipboardText.value
    if (!text) return false
    const clipboard = resolveClipboard()
    if (!clipboard?.writeText) return false
    pendingHostClipboardText.value = null
    void clipboard.writeText(text).catch(() => {})
    return true
  }

  /** `document` `copy` handler (`app.js:170`) — read the host clipboard, push to VNC. */
  function syncHostClipboard(): void {
    setTimeout(() => {
      void (async () => {
        const clipboard = resolveClipboard()
        if (!clipboard?.readText) return
        try {
          const text = await clipboard.readText()
          if (text) sendToVnc(text)
        } catch {
          /* read permission denied */
        }
      })()
    }, copyReadDelayMs)
  }

  /**
   * Feed a raw WS frame to the clipboard bridge. Returns `true` when it was a
   * handled `clipboard_update`. Safe to call from a shared session socket.
   */
  function handleMessage(raw: unknown): boolean {
    const update = parseClipboardUpdate(raw)
    if (!update) return false
    latestDesktopClipboard.value = update.text
    void handleVncClipboard(update.text, false)
    return true
  }

  function startPolling(): void {
    if (pollHandle !== null) return
    polling.value = true
    pollHandle = setInterval(() => {
      if (connected.value) return
      if (!isActive()) return
      if (resolveDocument()?.visibilityState !== 'visible') return
      void syncFromVnc(false)
    }, pollIntervalMs)
  }

  function stopPolling(): void {
    if (pollHandle !== null) clearInterval(pollHandle)
    pollHandle = null
    polling.value = false
  }

  function scheduleReconnect(): void {
    if (stopped || reconnectHandle !== null) return
    reconnectHandle = setTimeout(() => {
      reconnectHandle = null
      openSocket()
    }, reconnectDelayMs)
  }

  function openSocket(): void {
    if (stopped || socket.value !== null) return
    let sock: ClipboardSocket
    try {
      sock = factory(resolveUrl())
    } catch {
      // Socket construction failed (bad URL / unsupported): keep polling and retry.
      startPolling()
      scheduleReconnect()
      return
    }
    socket.value = sock

    sock.onopen = () => {
      connected.value = true
    }
    sock.onmessage = (event) => {
      handleMessage(event.data)
    }
    sock.onclose = () => {
      connected.value = false
      socket.value = null
      if (stopped) return
      startPolling()
      scheduleReconnect()
    }
    // `error` is always followed by `close`; the close handler drives recovery.
    sock.onerror = () => undefined
  }

  function disconnect(): void {
    stopPolling()
    if (reconnectHandle !== null) {
      clearTimeout(reconnectHandle)
      reconnectHandle = null
    }
    const sock = socket.value
    socket.value = null
    connected.value = false
    if (sock) {
      sock.onopen = null
      sock.onmessage = null
      sock.onclose = null
      sock.onerror = null
      try {
        sock.close()
      } catch {
        /* already closed */
      }
    }
  }

  function start(): void {
    if (!stopped) return
    stopped = false
    startPolling()
    openSocket()
  }

  function stop(): void {
    stopped = true
    disconnect()
  }

  function dispose(): void {
    stop()
    pendingHostClipboardText.value = null
  }

  if (getCurrentInstance()) onBeforeUnmount(dispose)

  if (options.autoConnect !== false) start()

  return {
    connected: readonly(connected),
    polling: readonly(polling),
    latestDesktopClipboard: readonly(latestDesktopClipboard),
    pendingHostClipboardText: readonly(pendingHostClipboardText),
    sendToVnc,
    handleVncClipboard,
    syncFromVnc,
    copyFromDesktopToHost,
    flushPendingHostClipboard,
    syncHostClipboard,
    handleMessage,
    start,
    stop,
    dispose,
  }
}

export type UseClipboard = ReturnType<typeof useClipboard>
