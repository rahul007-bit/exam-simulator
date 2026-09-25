import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { parseTimerTick, useTimer } from '@/composables/useTimer'
import type { TimerSocket } from '@/composables/useTimer'
import { useTimerStore } from '@/stores/timer'

/** Deterministic fake WebSocket driven by the tests. */
class FakeSocket implements TimerSocket {
  onopen: ((event: unknown) => void) | null = null
  onmessage: ((event: { data: unknown }) => void) | null = null
  onclose: ((event: unknown) => void) | null = null
  onerror: ((event: unknown) => void) | null = null

  constructor(readonly url: string) {}

  close(): void {
    /* no-op: tests drive onclose explicitly */
  }

  emitOpen(): void {
    this.onopen?.({})
  }

  emitMessage(payload: unknown): void {
    this.onmessage?.({ data: JSON.stringify(payload) })
  }

  emitClose(): void {
    this.onclose?.({})
  }
}

function jsonResponse(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    text: () => Promise.resolve(JSON.stringify(payload)),
  } as unknown as Response
}

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  setActivePinia(createPinia())
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('parseTimerTick', () => {
  it('parses timer_tick frames and ignores everything else', () => {
    const tick = parseTimerTick(
      JSON.stringify({ type: 'timer_tick', time_remaining_seconds: 42, server_timestamp: 7 }),
    )
    expect(tick?.time_remaining_seconds).toBe(42)
    expect(tick?.server_timestamp).toBe(7)

    expect(parseTimerTick(JSON.stringify({ type: 'clipboard_update', text: 'x' }))).toBeNull()
    expect(parseTimerTick('not json')).toBeNull()
    expect(parseTimerTick(undefined)).toBeNull()
  })
})

describe('useTimer — tick handling (FE-023 T1)', () => {
  it('applies timer_tick frames from the session WS', () => {
    const timer = useTimer({ autoConnect: false })
    const store = useTimerStore()
    // Use handleMessage directly to model a frame arriving on the session bus.
    expect(
      timer.handleMessage(
        JSON.stringify({ type: 'timer_tick', time_remaining_seconds: 900, server_timestamp: 1000 }),
      ),
    ).toBe(true)

    expect(store.remainingSeconds).toBe(900)
    expect(store.formatted).toBe('15:00')
    expect(timer.urgency.value).toBe('warning')
    expect(timer.connected.value).toBe(false)
  })

  it('ignores non-timer frames routed through the shared socket', () => {
    const timer = useTimer({ autoConnect: false })
    expect(timer.handleMessage(JSON.stringify({ type: 'clipboard_update', text: 'hi' }))).toBe(false)
    expect(timer.handleMessage('')).toBe(false)
  })

  it('marks the connection open and stops the fallback poll', async () => {
    const sockets: FakeSocket[] = []
    const timer = useTimer({
      createSocket: (url) => {
        const socket = new FakeSocket(url)
        sockets.push(socket)
        return socket
      },
    })

    expect(sockets).toHaveLength(1)
    sockets[0].emitOpen()
    expect(timer.connected.value).toBe(true)
    expect(timer.polling.value).toBe(false)

    await vi.advanceTimersByTimeAsync(5000)
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('useTimer — poll fallback (FE-023 T2)', () => {
  it('polls /api/timer while the WS is disconnected', async () => {
    const timer = useTimer({ createSocket: (url) => new FakeSocket(url) })
    const store = useTimerStore()
    fetchMock.mockResolvedValue(
      jsonResponse({ active: true, time_remaining_seconds: 600, time_limit_minutes: 120 }),
    )

    expect(timer.polling.value).toBe(true)
    await vi.advanceTimersByTimeAsync(5000)

    expect(fetchMock).toHaveBeenCalledWith('/api/timer', expect.anything())
    expect(store.remainingSeconds).toBe(600)
    expect(timer.connected.value).toBe(false)
  })

  it('keeps polling on transient poll errors', async () => {
    const timer = useTimer({ createSocket: (url) => new FakeSocket(url) })
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500))

    await vi.advanceTimersByTimeAsync(5000)
    await vi.advanceTimersByTimeAsync(5000)

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(timer.polling.value).toBe(true)
  })
})

describe('useTimer — reconnect and sync (FE-023 acceptance)', () => {
  it('reconnects after a drop and resynchronises from the server clock', async () => {
    const sockets: FakeSocket[] = []
    const timer = useTimer({
      createSocket: (url) => {
        const socket = new FakeSocket(url)
        sockets.push(socket)
        return socket
      },
      reconnectDelayMs: 3000,
    })
    const store = useTimerStore()

    sockets[0].emitOpen()
    sockets[0].emitMessage({ type: 'timer_tick', time_remaining_seconds: 500, server_timestamp: 100 })
    expect(store.remainingSeconds).toBe(500)

    sockets[0].emitClose()
    expect(timer.connected.value).toBe(false)
    expect(timer.polling.value).toBe(true)

    await vi.advanceTimersByTimeAsync(3000)
    expect(sockets).toHaveLength(2)

    sockets[1].emitOpen()
    expect(timer.connected.value).toBe(true)
    expect(timer.polling.value).toBe(false)

    sockets[1].emitMessage({ type: 'timer_tick', time_remaining_seconds: 300, server_timestamp: 305 })
    expect(store.remainingSeconds).toBe(300)
    expect(timer.urgency.value).toBe('critical')
  })

  it('interpolates remaining seconds from server_timestamp between ticks', async () => {
    let fakeNow = 0
    const timer = useTimer({
      createSocket: (url) => new FakeSocket(url),
      now: () => fakeNow,
      pollIntervalMs: 60_000,
    })
    const store = useTimerStore()

    timer.handleMessage(
      JSON.stringify({ type: 'timer_tick', server_timestamp: 1_000_000, time_remaining_seconds: 600 }),
    )
    expect(store.remainingSeconds).toBe(600)

    fakeNow = 5000
    await vi.advanceTimersByTimeAsync(1000)
    expect(store.remainingSeconds).toBe(595)
  })

  it('fires onExpired once and tears down when the timer reaches zero', () => {
    const onExpired = vi.fn()
    const timer = useTimer({ autoConnect: false, onExpired })

    timer.handleMessage(JSON.stringify({ type: 'timer_tick', time_remaining_seconds: 0 }))
    expect(timer.isExpired.value).toBe(true)
    expect(onExpired).toHaveBeenCalledTimes(1)

    timer.handleMessage(JSON.stringify({ type: 'timer_tick', time_remaining_seconds: 0 }))
    expect(onExpired).toHaveBeenCalledTimes(1)
  })
})

describe('useTimer — warning/critical states are colour only (FE-023 acceptance)', () => {
  function guard(remaining: number): { urgency: string; color: string; style: Record<string, string> } {
    const timer = useTimer({ autoConnect: false })
    timer.handleMessage(
      JSON.stringify({ type: 'timer_tick', time_remaining_seconds: remaining, server_timestamp: 1 }),
    )
    return {
      urgency: timer.urgency.value,
      color: timer.urgencyColorVar.value,
      style: timer.urgencyStyle.value,
    }
  }

  it('maps thresholds to the legacy warning/critical bands', () => {
    expect(guard(3600).urgency).toBe('normal')
    expect(guard(1799).urgency).toBe('warning')
    expect(guard(600).urgency).toBe('warning')
    expect(guard(599).urgency).toBe('critical')
    expect(guard(0).urgency).toBe('critical')
  })

  it('uses AA-safe semantic tokens, never raw colours', () => {
    expect(guard(900).color).toBe('var(--color-warning-text)')
    expect(guard(120).color).toBe('var(--color-danger-text)')
    expect(guard(3600).color).toBe('var(--color-text)')
  })

  it('applies colour only — no animation, pulse or glow', () => {
    const { style } = guard(120)
    expect(Object.keys(style)).toEqual(['color'])
    expect(style.color).toMatch(/^var\(--color-[a-z-]+\)$/)
    expect(JSON.stringify(style)).not.toMatch(/#[0-9a-fA-F]{3,6}/)
    expect(JSON.stringify(style)).not.toMatch(/animation|shadow|pulse|glow|blur/i)
  })
})
