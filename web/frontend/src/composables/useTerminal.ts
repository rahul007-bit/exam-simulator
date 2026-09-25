import { getCurrentInstance, onBeforeUnmount, readonly, ref, shallowRef } from 'vue'
import type { Ref } from 'vue'

/**
 * useTerminal (FE-025) — imperative transport for the XTerm island.
 *
 * Owns the `/ws/terminal/<sessionId>` connection and keeps the xterm instance
 * out of Vue's reactivity system. It deliberately depends only on a **structural**
 * view of xterm (`TerminalLike`) so this module stays free of the `@xterm/xterm`
 * import; the component is the only place that touches xterm directly.
 *
 * Server contract (unchanged, D-007 — see `web/server.py:1677`):
 *   - binary frames carry raw PTY I/O in both directions;
 *   - a JSON text frame `{"resize":{"rows":R,"cols":C}}` resizes the PTY.
 * The server replays the Redis scrollback buffer immediately on (re)connect;
 * `replayScrollback()` is the client-side fallback for explicit replays.
 */

/** Minimal disposable returned by xterm's `onData`/`onResize` registrations. */
export interface TerminalDisposable {
  dispose(): void
}

/** Structural (dependency-free) subset of an xterm `Terminal`. */
export interface TerminalLike {
  rows: number
  cols: number
  write(data: string | Uint8Array): void
  onData(handler: (data: string) => void): TerminalDisposable
  onResize(handler: (size: { rows: number; cols: number }) => void): TerminalDisposable
}

/** Structural view of the socket we drive (matches the DOM `WebSocket`). */
export interface TerminalSocketLike {
  binaryType: string
  readyState: number
  send(data: string | ArrayBufferLike | Blob | ArrayBufferView): void
  close(code?: number, reason?: string): void
  onopen: ((event: unknown) => void) | null
  onmessage: ((event: { data: unknown }) => void) | null
  onclose: ((event: { code?: number; reason?: string }) => void) | null
  onerror: ((event: unknown) => void) | null
}

export type TerminalStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error'

export interface UseTerminalOptions {
  /** Session id (or getter) used to build the default URL. */
  sessionId: string | (() => string | null | undefined)
  /** Ref holding the live terminal (installed by the component after `open`). */
  terminal: Ref<TerminalLike | null>
  /** Explicit socket URL. Takes precedence over `sessionId`. */
  url?: string | ((sessionId: string | null) => string)
  /** Maximum output chunks retained for local replay. Default 200. */
  bufferLimit?: number
  /** Connect immediately on creation. Default `false` (component drives it). */
  autoConnect?: boolean
  /** Injectable socket factory (tests). Defaults to the global `WebSocket`. */
  createSocket?: (url: string) => TerminalSocketLike
  onOpen?: () => void
  onClose?: (event: { code?: number; reason?: string }) => void
  onError?: (event: unknown) => void
}

export const DEFAULT_TERMINAL_BUFFER_LIMIT = 200

/** `WebSocket` readyState values, declared locally to avoid a DOM global dep. */
export const SOCKET_CONNECTING = 0
export const SOCKET_OPEN = 1

function defaultSocketUrl(sessionId: string | null): string {
  const base =
    typeof window !== 'undefined'
      ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`
      : ''
  const suffix = sessionId ? `/${encodeURIComponent(sessionId)}` : ''
  return `${base}/ws/terminal${suffix}`
}

function defaultCreateSocket(url: string): TerminalSocketLike {
  return new WebSocket(url) as unknown as TerminalSocketLike
}

export function useTerminal(options: UseTerminalOptions) {
  const terminal = options.terminal
  const status = ref<TerminalStatus>('idle')
  const connected = ref(false)
  const socket = shallowRef<TerminalSocketLike | null>(null)

  const bufferLimit = Math.max(0, options.bufferLimit ?? DEFAULT_TERMINAL_BUFFER_LIMIT)
  const factory = options.createSocket ?? defaultCreateSocket

  // Plain (non-reactive) scratch state: xterm data must never be proxied.
  let scrollback: Uint8Array[] = []
  let dataDisposable: TerminalDisposable | null = null
  let resizeDisposable: TerminalDisposable | null = null
  let tornDown = false

  function resolveSessionId(): string | null {
    const raw = typeof options.sessionId === 'function' ? options.sessionId() : options.sessionId
    const trimmed = typeof raw === 'string' ? raw.trim() : ''
    return trimmed.length > 0 ? trimmed : null
  }

  function resolveUrl(sessionId: string | null): string {
    if (typeof options.url === 'function') return options.url(sessionId)
    if (typeof options.url === 'string') return options.url
    return defaultSocketUrl(sessionId)
  }

  function appendScrollback(chunk: Uint8Array): void {
    if (bufferLimit === 0) return
    scrollback.push(chunk)
    if (scrollback.length > bufferLimit) {
      scrollback.splice(0, scrollback.length - bufferLimit)
    }
  }

  function writeToTerminal(data: string | Uint8Array): void {
    const term = terminal.value
    if (term) term.write(data)
  }

  /** Feed a raw WS frame to the terminal; binary is I/O, text is output/resize. */
  function handleMessage(raw: unknown): void {
    if (raw instanceof ArrayBuffer) {
      const bytes = new Uint8Array(raw)
      appendScrollback(bytes)
      writeToTerminal(bytes)
      return
    }
    if (ArrayBuffer.isView(raw)) {
      const bytes = new Uint8Array(raw.buffer, raw.byteOffset, raw.byteLength)
      appendScrollback(bytes)
      writeToTerminal(bytes)
      return
    }
    if (typeof raw === 'string') {
      appendScrollback(new TextEncoder().encode(raw))
      writeToTerminal(raw)
    }
  }

  /** Send raw input (string or bytes) when the socket is open. */
  function send(data: string | Uint8Array): boolean {
    const sock = socket.value
    if (!sock || sock.readyState !== SOCKET_OPEN) return false
    sock.send(data)
    return true
  }

  /** Send the PTY resize frame; falls back to the live terminal dimensions. */
  function sendResize(rows?: number, cols?: number): void {
    const term = terminal.value
    const r = rows ?? term?.rows ?? 24
    const c = cols ?? term?.cols ?? 80
    send(JSON.stringify({ resize: { rows: r, cols: c } }))
  }

  function bindTerminal(): void {
    const term = terminal.value
    if (!term || dataDisposable) return
    dataDisposable = term.onData((data) => {
      send(data)
    })
    resizeDisposable = term.onResize(() => {
      sendResize()
    })
  }

  function unbindTerminal(): void {
    dataDisposable?.dispose()
    resizeDisposable?.dispose()
    dataDisposable = null
    resizeDisposable = null
  }

  /** Close the socket and detach terminal handlers, retaining scrollback. */
  function disconnect(): void {
    unbindTerminal()
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
    if (status.value !== 'idle') status.value = 'closed'
  }

  function connect(): void {
    if (tornDown) return
    const existing = socket.value
    if (
      existing &&
      (existing.readyState === SOCKET_OPEN || existing.readyState === SOCKET_CONNECTING)
    ) {
      return
    }
    disconnect()

    const sessionId = resolveSessionId()
    let sock: TerminalSocketLike
    try {
      sock = factory(resolveUrl(sessionId))
    } catch (error) {
      status.value = 'error'
      options.onError?.(error)
      return
    }

    sock.binaryType = 'arraybuffer'
    socket.value = sock
    status.value = 'connecting'

    sock.onopen = () => {
      if (socket.value !== sock) return
      status.value = 'open'
      connected.value = true
      bindTerminal()
      sendResize()
      options.onOpen?.()
    }
    sock.onmessage = (event) => {
      if (socket.value !== sock) return
      handleMessage(event.data)
    }
    sock.onclose = (event) => {
      if (socket.value === sock) {
        socket.value = null
        connected.value = false
        status.value = 'closed'
        unbindTerminal()
      }
      options.onClose?.(event)
    }
    sock.onerror = (event) => {
      if (socket.value !== sock) return
      status.value = 'error'
      options.onError?.(event)
    }
  }

  function reconnect(): void {
    disconnect()
    connect()
  }

  /** Re-write buffered output into the terminal (local scrollback replay). */
  function replayScrollback(): void {
    for (const chunk of scrollback) writeToTerminal(chunk)
  }

  /** Snapshot of the retained scrollback chunks (newest last). */
  function getScrollback(): readonly Uint8Array[] {
    return scrollback.slice()
  }

  function clearScrollback(): void {
    scrollback = []
  }

  function dispose(): void {
    tornDown = true
    disconnect()
    status.value = 'idle'
    clearScrollback()
  }

  if (getCurrentInstance()) onBeforeUnmount(dispose)

  if (options.autoConnect) connect()

  return {
    status: readonly(status),
    connected: readonly(connected),
    connect,
    disconnect,
    reconnect,
    dispose,
    send,
    sendResize,
    replayScrollback,
    getScrollback,
    clearScrollback,
  }
}
