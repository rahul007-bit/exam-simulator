import { getCurrentInstance, onBeforeUnmount, onMounted } from 'vue'

/**
 * useVnc (FE-026) — URL + `postMessage` helpers for the noVNC desktop island.
 *
 * Strict parity with the legacy candidate client (D-007, `web/server.py`):
 * the iframe is served by the `/novnc` StaticFiles mount and its websockify
 * `path` points at the `/novnc/ws/desktop/<sessionId>` proxy route. The query
 * string is assembled by hand — **not** `URLSearchParams` — because the latter
 * percent-encodes the `/` in `ws/desktop/<sid>` and would change the URL
 * contract the server and noVNC expect.
 *
 * Legacy contract:
 *   - URL: candidate load, view-only observe
 *   - allow: the iframe `allow` attribute
 *   - inbound messages: `VNC_CLIPBOARD` / `VNC_DISCONNECTED`
 *   - outbound clipboard: `{ type: 'SET_CLIPBOARD', text }`
 */

/** iframe `allow` attribute, preserved verbatim from the legacy client. */
export const VNC_ALLOW = 'clipboard-read *; clipboard-write *; fullscreen *; keyboard-map *'

/** Session id sentinel used when no live session exists (legacy `|| 'active'`). */
export const VNC_DEFAULT_SESSION = 'active'

/** Outbound message type: host → noVNC clipboard sync. */
export const VNC_SET_CLIPBOARD = 'SET_CLIPBOARD'

/** Inbound message type: noVNC → host clipboard. */
export const VNC_CLIPBOARD_EVENT = 'VNC_CLIPBOARD'

/** Inbound message type: noVNC → host disconnect. */
export const VNC_DISCONNECTED_EVENT = 'VNC_DISCONNECTED'

export interface VncClipboardMessage {
  type: typeof VNC_CLIPBOARD_EVENT
  text: string
}

export interface VncDisconnectedMessage {
  type: typeof VNC_DISCONNECTED_EVENT
}

export type VncInboundMessage = VncClipboardMessage | VncDisconnectedMessage

export interface BuildNoVncUrlOptions {
  /** Observe mode: adds `view_only=true`. */
  viewOnly?: boolean
}

/**
 * Build the compiled/relative noVNC URL the FastAPI server exposes.
 *
 * Candidate: `/novnc/vnc.html?autoconnect=true&resize=remote&reconnect=true&path=ws/desktop/<sid>`
 * View-only: `...&view_only=true&path=ws/desktop/<sid>` (parameter order preserved).
 */
export function buildNoVncUrl(
  sessionId: string | null | undefined,
  options: BuildNoVncUrlOptions = {},
): string {
  const trimmed = typeof sessionId === 'string' ? sessionId.trim() : ''
  const sid = trimmed.length > 0 ? trimmed : VNC_DEFAULT_SESSION

  const params = ['autoconnect=true', 'resize=remote', 'reconnect=true']
  if (options.viewOnly) params.push('view_only=true')
  params.push(`path=ws/desktop/${encodeURIComponent(sid)}`)

  return `/novnc/vnc.html?${params.join('&')}`
}

/** Narrow an unknown `MessageEvent.data` payload to a recognised VNC message. */
export function parseVncMessage(data: unknown): VncInboundMessage | null {
  if (!data || typeof data !== 'object') return null
  const type = (data as { type?: unknown }).type

  if (type === VNC_DISCONNECTED_EVENT) return { type: VNC_DISCONNECTED_EVENT }
  if (type === VNC_CLIPBOARD_EVENT) {
    const text = (data as { text?: unknown }).text
    if (typeof text === 'string') return { type: VNC_CLIPBOARD_EVENT, text }
  }
  return null
}

/** Post a message into the desktop iframe; returns whether it was delivered. */
export function postToFrame(frame: HTMLIFrameElement | null, message: unknown): boolean {
  const target = frame?.contentWindow
  if (!target) return false
  try {
    target.postMessage(message, '*')
    return true
  } catch {
    return false
  }
}

/** Sync host clipboard text to the desktop island (`syncTextToVnc`). */
export function postClipboardToFrame(frame: HTMLIFrameElement | null, text: string): boolean {
  if (!text) return false
  return postToFrame(frame, { type: VNC_SET_CLIPBOARD, text })
}

export interface UseVncOptions {
  /** Called with the text when the island reports `VNC_CLIPBOARD`. */
  onClipboard?: (text: string) => void
  /** Called when the island reports `VNC_DISCONNECTED`. */
  onDisconnected?: () => void
  /** Only accept messages whose `source` is this window (the island iframe). */
  source?: () => Window | null | undefined
  /** Attach the listener immediately on creation (default `false`). */
  autoStart?: boolean
  /** Message target (tests). Defaults to the global `window`. */
  target?: Window
}

/**
 * Register a `message` listener that surfaces the legacy noVNC events. The
 * component drives `start`/`stop` from the iframe lifecycle; `setSource` scopes
 * delivery to the island so unrelated window messages are ignored.
 */
export function useVnc(options: UseVncOptions = {}) {
  const target: Window | undefined = options.target ?? (typeof window !== 'undefined' ? window : undefined)
  let sourceWindow: Window | null = null
  let listening = false

  function handleMessage(event: MessageEvent): void {
    if (sourceWindow && event.source && event.source !== sourceWindow) return
    const message = parseVncMessage(event.data)
    if (!message) return
    if (message.type === VNC_CLIPBOARD_EVENT) options.onClipboard?.(message.text)
    else options.onDisconnected?.()
  }

  function setSource(frame: HTMLIFrameElement | null | undefined): void {
    sourceWindow = frame?.contentWindow ?? null
  }

  function start(): void {
    if (listening || !target) return
    target.addEventListener('message', handleMessage)
    listening = true
  }

  function stop(): void {
    if (!listening || !target) return
    target.removeEventListener('message', handleMessage)
    listening = false
  }

  if (getCurrentInstance()) {
    onMounted(start)
    onBeforeUnmount(stop)
  } else if (options.autoStart) {
    start()
  }

  return {
    start,
    stop,
    setSource,
    postToFrame,
    postClipboardToFrame,
  }
}
