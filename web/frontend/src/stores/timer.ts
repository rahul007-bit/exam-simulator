import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as timerApi from '@/api/timer'
import type { TimerResponse, TimerTick } from '@/api/timer'
import type { SessionResponse } from '@/api/session'

/**
 * Warning/critical thresholds (seconds remaining).
 *
 * These mirror the legacy server-authoritative timer controller
 * (`updateTimerDisplay`): below 10 minutes the timer is critical, below 30
 * minutes it is a warning. Both states are communicated with **colour only**
 * (no pulse/glow), using the AA-safe semantic text tokens (FE-023).
 */
export const CRITICAL_THRESHOLD_SECONDS = 600
export const WARNING_THRESHOLD_SECONDS = 1800

export function formatDuration(totalSeconds: number | null | undefined): string {
  if (totalSeconds === null || totalSeconds === undefined || Number.isNaN(totalSeconds))
    return '--:--'
  const safe = Math.max(0, Math.floor(totalSeconds))
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const seconds = safe % 60
  const pad = (value: number) => String(value).padStart(2, '0')
  return hours > 0 ? `${hours}:${pad(minutes)}:${pad(seconds)}` : `${pad(minutes)}:${pad(seconds)}`
}

export type TimerUrgency = 'normal' | 'warning' | 'critical'

export const useTimerStore = defineStore('timer', () => {
  const active = ref(false)
  const remainingSeconds = ref<number | null>(null)
  const timeLimitMinutes = ref<number | null>(null)
  const serverTimestamp = ref<number | null>(null)
  const startTimestamp = ref<number | null>(null)
  const endTimestamp = ref<number | null>(null)
  const totalSeconds = ref<number | null>(null)
  const elapsedSeconds = ref<number | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  /** `server_now * 1000 - client_now`; used to interpolate between server ticks. */
  const serverOffsetMs = ref<number | null>(null)

  const isExpired = computed(() => remainingSeconds.value !== null && remainingSeconds.value <= 0)
  const formatted = computed(() => formatDuration(remainingSeconds.value))

  /** Warning/critical states use colour only (no pulse/glow) — FE-023. */
  const urgency = computed<TimerUrgency>(() => {
    const remaining = remainingSeconds.value
    if (remaining === null) return 'normal'
    if (remaining < CRITICAL_THRESHOLD_SECONDS) return 'critical'
    if (remaining < WARNING_THRESHOLD_SECONDS) return 'warning'
    return 'normal'
  })

  /**
   * AA-safe semantic token for the current urgency. Consumers must apply this
   * as a plain `color` (never an animation/glow) so the timer relies on colour
   * alone to signal state (FE-023).
   */
  const urgencyColorVar = computed(() => {
    switch (urgency.value) {
      case 'critical':
        return 'var(--color-danger-text)'
      case 'warning':
        return 'var(--color-warning-text)'
      default:
        return 'var(--color-text)'
    }
  })

  /** Colour-only style object for the timer text. */
  const urgencyStyle = computed<Record<string, string>>(() => ({ color: urgencyColorVar.value }))

  /** Anchor the local clock to the server clock (`server_timestamp`, seconds). */
  function setServerClock(serverSeconds: number, nowMs: number = Date.now()): void {
    serverTimestamp.value = serverSeconds
    serverOffsetMs.value = serverSeconds * 1000 - nowMs
  }

  /**
   * Recompute `remainingSeconds` from the authoritative end timestamp and the
   * last known server clock offset. No-op until both are known, which keeps the
   * store usable with payloads that only carry `time_remaining_seconds`.
   */
  function recalculate(nowMs: number = Date.now()): void {
    if (endTimestamp.value === null || serverOffsetMs.value === null) return
    const serverNowMs = nowMs + serverOffsetMs.value
    const remaining = Math.round((endTimestamp.value * 1000 - serverNowMs) / 1000)
    remainingSeconds.value = Math.max(0, remaining)
  }

  function applyTimer(timer: TimerResponse, nowMs: number = Date.now()): void {
    active.value = timer.active
    remainingSeconds.value = timer.time_remaining_seconds ?? null
    timeLimitMinutes.value = timer.time_limit_minutes ?? null
    serverTimestamp.value = timer.server_timestamp ?? null
    startTimestamp.value = timer.start_timestamp ?? null
    endTimestamp.value = timer.end_timestamp ?? null
    totalSeconds.value = timer.total_seconds ?? null
    elapsedSeconds.value = timer.elapsed_seconds ?? null
    error.value = timer.error ?? null
    if (typeof timer.server_timestamp === 'number') setServerClock(timer.server_timestamp, nowMs)
    if (endTimestamp.value !== null) recalculate(nowMs)
  }

  /**
   * Apply a `timer_tick` WebSocket payload (defined in PLAN.md §3). When the
   * tick carries both `time_remaining_seconds` and `server_timestamp` it is
   * anchored to an absolute `end_timestamp`, letting the display interpolate
   * smoothly from the **server clock** instead of trusting a skew-prone client.
   */
  function applyTick(tick: TimerTick, nowMs: number = Date.now()): void {
    if (
      typeof tick.server_timestamp === 'number' &&
      typeof tick.time_remaining_seconds === 'number'
    ) {
      setServerClock(tick.server_timestamp, nowMs)
      endTimestamp.value = tick.server_timestamp + tick.time_remaining_seconds
    }
    if (tick.time_remaining_seconds !== undefined)
      remainingSeconds.value = tick.time_remaining_seconds
    if (tick.time_limit_minutes !== undefined) timeLimitMinutes.value = tick.time_limit_minutes
    if (tick.server_timestamp !== undefined) serverTimestamp.value = tick.server_timestamp
    if (tick.start_timestamp !== undefined) startTimestamp.value = tick.start_timestamp
    if (tick.end_timestamp !== undefined) endTimestamp.value = tick.end_timestamp
    if (tick.total_seconds !== undefined) totalSeconds.value = tick.total_seconds
    if (tick.elapsed_seconds !== undefined) elapsedSeconds.value = tick.elapsed_seconds
  }

  /** Seed the timer from a `/api/session` payload (used on initial load). */
  function syncFromSession(session: SessionResponse, nowMs: number = Date.now()): void {
    if (session.active !== true) {
      active.value = false
      remainingSeconds.value = null
      return
    }
    active.value = true
    remainingSeconds.value = session.time_remaining_seconds
    timeLimitMinutes.value = session.time_limit_minutes ?? null
    serverTimestamp.value = session.server_timestamp
    startTimestamp.value = session.start_timestamp ?? null
    endTimestamp.value = session.end_timestamp ?? null
    if (typeof session.server_timestamp === 'number') setServerClock(session.server_timestamp, nowMs)
    if (endTimestamp.value !== null) recalculate(nowMs)
  }

  /** Clear all timer state (e.g. after submit/reset). */
  function reset(): void {
    active.value = false
    remainingSeconds.value = null
    timeLimitMinutes.value = null
    serverTimestamp.value = null
    startTimestamp.value = null
    endTimestamp.value = null
    totalSeconds.value = null
    elapsedSeconds.value = null
    serverOffsetMs.value = null
    error.value = null
  }

  async function fetchTimer(): Promise<TimerResponse | null> {
    loading.value = true
    error.value = null
    try {
      const timer = await timerApi.getTimer()
      applyTimer(timer)
      return timer
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    active,
    remainingSeconds,
    timeLimitMinutes,
    serverTimestamp,
    startTimestamp,
    endTimestamp,
    totalSeconds,
    elapsedSeconds,
    serverOffsetMs,
    loading,
    error,
    isExpired,
    formatted,
    urgency,
    urgencyColorVar,
    urgencyStyle,
    setServerClock,
    recalculate,
    applyTimer,
    applyTick,
    syncFromSession,
    reset,
    fetchTimer,
  }
})
