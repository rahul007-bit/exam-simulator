import { computed, getCurrentInstance, onBeforeUnmount, readonly, ref, shallowRef } from 'vue'

import type { TimerTick } from '@/api/timer'
import { useTimerStore } from '@/stores/timer'

/**
 * Timer composable (FE-023).
 *
 * Consumes `timer_tick` frames from the session WebSocket event bus and keeps
 * the Pinia timer store in sync with the **server clock** (`server_timestamp`).
 * When the socket is disconnected it falls back to polling `/api/timer`, and it
 * re-connects (with the legacy 3s delay) and resynchronises automatically.
 *
 * The socket is injectable (`createSocket`) so the behaviour can be unit tested
 * against a fake WebSocket and deterministic timers. A second entry point,
 * `handleMessage()`, lets a caller multiplex frames from an already-open
 * session socket (e.g. the future `useSessionWs`) without opening a duplicate
 * connection.
 */

/** Minimal structural type for the socket we depend on (matches `WebSocket`). */
export interface TimerSocket {
  close(code?: number, reason?: string): void
  onopen: ((event: unknown) => void) | null
  onmessage: ((event: { data: unknown }) => void) | null
  onclose: ((event: unknown) => void) | null
  onerror: ((event: unknown) => void) | null
}

export interface UseTimerOptions {
  /** Explicit socket URL. Takes precedence over `sessionId`. */
  url?: string | (() => string)
  /** Session id used to build the default `/ws/session/<id>` URL. */
  sessionId?: string
  /** Injectable socket factory (tests). Defaults to the global `WebSocket`. */
  createSocket?: (url: string) => TimerSocket
  /** Poll interval used while the socket is disconnected (ms). Default 5000. */
  pollIntervalMs?: number
  /** Delay before attempting to re-open a closed socket (ms). Default 3000. */
  reconnectDelayMs?: number
  /** Local display tick interval for server-clock interpolation (ms). Default 1000. */
  tickIntervalMs?: number
  /** Clock injection for deterministic tests. Defaults to `Date.now`. */
  now?: () => number
  /** Connect immediately on creation. Default `true`. */
  autoConnect?: boolean
  /** Called once when the timer crosses into expiry. */
  onExpired?: () => void
}

export const DEFAULT_POLL_INTERVAL_MS = 5000
export const DEFAULT_RECONNECT_DELAY_MS = 3000
export const DEFAULT_TICK_INTERVAL_MS = 1000

function defaultSocketUrl(sessionId: string): string {
  if (typeof window === 'undefined') return `/ws/session/${sessionId}`
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/session/${sessionId}`
}

function defaultCreateSocket(url: string): TimerSocket {
  return new WebSocket(url) as unknown as TimerSocket
}

/** Extract a typed `timer_tick` payload from a raw WS frame, if it is one. */
export function parseTimerTick(raw: unknown): TimerTick | null {
  if (typeof raw !== 'string') return null
  try {
    const data = JSON.parse(raw) as TimerTick & { type?: string }
    if (!data || data.type !== 'timer_tick') return null
    return data
  } catch {
    return null
  }
}

export function useTimer(options: UseTimerOptions = {}) {
  const store = useTimerStore()

  const connected = ref(false)
  const polling = ref(false)
  const socket = shallowRef<TimerSocket | null>(null)

  const now = options.now ?? (() => Date.now())
  const pollIntervalMs = options.pollIntervalMs ?? DEFAULT_POLL_INTERVAL_MS
  const reconnectDelayMs = options.reconnectDelayMs ?? DEFAULT_RECONNECT_DELAY_MS
  const tickIntervalMs = options.tickIntervalMs ?? DEFAULT_TICK_INTERVAL_MS
  const factory = options.createSocket ?? defaultCreateSocket

  let pollHandle: ReturnType<typeof setInterval> | null = null
  let reconnectHandle: ReturnType<typeof setTimeout> | null = null
  let tickHandle: ReturnType<typeof setInterval> | null = null
  let stopped = true
  let expiredNotified = false

  function resolveUrl(): string {
    if (typeof options.url === 'function') return options.url()
    if (typeof options.url === 'string') return options.url
    return defaultSocketUrl(options.sessionId ?? 'active')
  }

  function stopPolling(): void {
    if (pollHandle !== null) clearInterval(pollHandle)
    pollHandle = null
    polling.value = false
  }

  async function pollOnce(): Promise<void> {
    if (connected.value) return
    const timer = await store.fetchTimer()
    // A disconnected/inactive session stops the fallback, mirroring legacy
    // `fetchServerTimer` which tears the poller down when `active === false`.
    if (timer !== null && timer.active === false) stopPolling()
  }

  function startPolling(): void {
    if (pollHandle !== null) return
    polling.value = true
    pollHandle = setInterval(() => {
      void pollOnce()
    }, pollIntervalMs)
  }

  function maybeExpire(): void {
    if (expiredNotified || !store.isExpired) return
    expiredNotified = true
    stop()
    options.onExpired?.()
  }

  function startTicker(): void {
    if (tickHandle !== null) return
    tickHandle = setInterval(() => {
      store.recalculate(now())
      maybeExpire()
    }, tickIntervalMs)
  }

  function clearTicker(): void {
    if (tickHandle !== null) clearInterval(tickHandle)
    tickHandle = null
  }

  function scheduleReconnect(): void {
    if (stopped || reconnectHandle !== null) return
    reconnectHandle = setTimeout(() => {
      reconnectHandle = null
      openSocket()
    }, reconnectDelayMs)
  }

  /**
   * Feed a raw WS frame to the timer. Returns `true` when it was a handled
   * `timer_tick`. Safe to call from a shared session socket.
   */
  function handleMessage(raw: unknown): boolean {
    const tick = parseTimerTick(raw)
    if (tick === null) return false
    store.applyTick(tick, now())
    maybeExpire()
    return true
  }

  function openSocket(): void {
    if (stopped || socket.value !== null) return
    let sock: TimerSocket
    try {
      sock = factory(resolveUrl())
    } catch {
      // Socket construction failed (bad URL / unsupported): keep the poll
      // fallback and retry the connection later.
      startPolling()
      scheduleReconnect()
      return
    }
    socket.value = sock

    sock.onopen = () => {
      connected.value = true
      stopPolling()
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

  function start(): void {
    if (!stopped) return
    stopped = false
    expiredNotified = false
    startTicker()
    startPolling()
    openSocket()
  }

  function stop(): void {
    stopped = true
    clearTicker()
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

  if (getCurrentInstance()) onBeforeUnmount(stop)

  if (options.autoConnect !== false) start()

  return {
    connected: readonly(connected),
    polling: readonly(polling),
    active: computed(() => store.active),
    remainingSeconds: computed(() => store.remainingSeconds),
    formatted: computed(() => store.formatted),
    urgency: computed(() => store.urgency),
    urgencyColorVar: computed(() => store.urgencyColorVar),
    urgencyStyle: computed(() => store.urgencyStyle),
    isExpired: computed(() => store.isExpired),
    handleMessage,
    start,
    stop,
  }
}
