import { computed, getCurrentInstance, onBeforeUnmount, readonly, ref, shallowRef } from 'vue'
import type { ComputedRef, Ref } from 'vue'

/**
 * useReplay (FE-029) — the asciinema `.cast` replay engine for the recordings
 * island. Ports the legacy candidate replay (`parseCastRecording` /
 * `playReplay` / `replayTick` / `seekReplay`) into a
 * ref-driven composable that keeps the xterm instance out of Vue's reactivity
 * system exactly like `useTerminal`.
 *
 * Cast format handled (asciinema v2, emitted by `core/recorder.py`):
 *
 *   {"version": 2, "width": 80, "height": 24, ...}   <- first-line JSON header
 *   [time, "o", "data"]                              <- terminal output
 *   [time, "i", "data"]                              <- terminal input (ignored)
 *   [time, "r", "colsxrows"]                         <- resize (ignored)
 *   [time, "m", "marker text"]                       <- event marker (ignored)
 *
 * Only `"o"` frames are written to the terminal; the rest are retained so a
 * future timeline can use them. The v1 header (a bare version number) is not
 * supported, matching the legacy parser.
 */

export type CastFrameType = 'o' | 'i' | 'r' | 'm' | (string & {})

export interface CastFrame {
  /** Seconds since the recording start. */
  time: number
  /** Asciinema event type (`o`, `i`, `r`, `m`). */
  type: CastFrameType
  /** Frame payload (terminal output for `o`). */
  data: string
}

export interface CastHeader {
  version?: number
  width?: number
  height?: number
  timestamp?: number
  duration?: number
  title?: string
  env?: Record<string, string>
  [key: string]: unknown
}

export interface ParsedCast {
  header: CastHeader | null
  frames: CastFrame[]
  /** Last frame time, or the header `duration` when it is larger. */
  duration: number
}

/**
 * Parse an asciinema v2 `.cast` payload. Malformed lines/frames are skipped
 * (parity with the legacy `try { JSON.parse } catch {}` behaviour) so a single
 * bad line never breaks a replay.
 */
export function parseCastRecording(castText: string): ParsedCast {
  const frames: CastFrame[] = []
  let header: CastHeader | null = null
  let duration = 0

  if (typeof castText !== 'string' || castText.length === 0) {
    return { header, frames, duration }
  }

  const lines = castText.split(/\r?\n/)
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].trim()
    if (!line) continue

    // The v2 header is a JSON object on the first non-empty line.
    if (i === 0 && line.startsWith('{')) {
      try {
        const parsed: unknown = JSON.parse(line)
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          header = parsed as CastHeader
          if (typeof header.duration === 'number' && header.duration > duration) {
            duration = header.duration
          }
          continue
        }
      } catch {
        // Fall through and try to interpret it as a frame.
      }
    }

    if (!line.startsWith('[')) continue
    try {
      const frame: unknown = JSON.parse(line)
      if (!Array.isArray(frame) || frame.length < 3) continue
      const time = typeof frame[0] === 'number' ? frame[0] : Number.parseFloat(String(frame[0]))
      const type = frame[1]
      const data = frame[2]
      if (!Number.isFinite(time) || typeof type !== 'string' || typeof data !== 'string') continue
      frames.push({ time, type, data })
      if (time > duration) duration = time
    } catch {
      // Skip malformed frames.
    }
  }

  // The recorder writes frames in order; sort defensively for older exports.
  frames.sort((a, b) => a.time - b.time)

  return { header, frames, duration }
}

/** Structural (dependency-free) subset of an xterm `Terminal` we replay into. */
export interface ReplayTerminalLike {
  reset(): void
  write(data: string): void
}

/** Minimal event shape needed to sync a timeline to the replay position. */
export interface ReplayEventLike {
  rel_time?: number | null
}

export interface UseReplayOptions {
  /** Ref holding the live terminal (installed by the component after `open`). */
  terminal: Ref<ReplayTerminalLike | null>
  /** Duration to use when the cast has no usable timing (seconds). */
  durationFallback?: number | (() => number)
}

export const MIN_REPLAY_SPEED = 0.5
export const MAX_REPLAY_SPEED = 10

/** `mm:ss`, or `hh:mm:ss` past an hour — parity with legacy `formatDurationSeconds`. */
export function formatReplayTime(seconds: number | null | undefined): string {
  const total = Math.max(0, Math.floor(seconds ?? 0))
  const mins = Math.floor(total / 60)
  const remSec = total % 60
  const hrs = Math.floor(mins / 60)
  const remMin = mins % 60
  if (hrs > 0) {
    return `${String(hrs).padStart(2, '0')}:${String(remMin).padStart(2, '0')}:${String(remSec).padStart(2, '0')}`
  }
  return `${String(remMin).padStart(2, '0')}:${String(remSec).padStart(2, '0')}`
}

function nowMs(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now()
}

export function useReplay(options: UseReplayOptions) {
  const terminal = options.terminal
  const frames = shallowRef<CastFrame[]>([])
  const header = shallowRef<CastHeader | null>(null)
  const events = shallowRef<readonly ReplayEventLike[]>([])
  const duration = ref(0)
  const currentTime = ref(0)
  const isPlaying = ref(false)
  const speed = ref(1)

  // Plain (non-reactive) playback cursor + animation frame handle.
  let nextIndex = 0
  let lastFrameTime = 0
  let rafId: number | null = null
  let tornDown = false

  const progress = computed(() =>
    duration.value > 0 ? Math.min(1, Math.max(0, currentTime.value / duration.value)) : 0,
  )

  /**
   * Index of the last timeline event at or before the playhead (`-1` before the
   * first event). Drives the sidebar highlight in `ReplayPlayer`.
   */
  const activeEventIndex = computed(() => {
    const list = events.value
    let active = -1
    for (let i = 0; i < list.length; i += 1) {
      const t = list[i].rel_time
      if (typeof t === 'number' && Number.isFinite(t) && t <= currentTime.value) active = i
    }
    return active
  })

  function resolveFallback(): number {
    const raw = typeof options.durationFallback === 'function'
      ? options.durationFallback()
      : options.durationFallback
    return typeof raw === 'number' && Number.isFinite(raw) && raw > 0 ? raw : 0
  }

  function writeFrame(data: string): void {
    const term = terminal.value
    if (term) term.write(data)
  }

  function resetTerminal(): void {
    const term = terminal.value
    if (!term) return
    try {
      term.reset()
    } catch {
      // Terminal already disposed.
    }
  }

  function schedule(): void {
    if (rafId !== null) return
    rafId = requestAnimationFrame(tick)
  }

  function stopLoop(): void {
    if (rafId !== null) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
  }

  function tick(): void {
    rafId = null
    if (!isPlaying.value || tornDown) return

    const now = nowMs()
    const delta = ((now - lastFrameTime) / 1000) * speed.value
    lastFrameTime = now

    const nextTime = Math.min(duration.value, currentTime.value + delta)
    while (nextIndex < frames.value.length && frames.value[nextIndex].time <= nextTime) {
      const frame = frames.value[nextIndex]
      if (frame.type === 'o') writeFrame(frame.data)
      nextIndex += 1
    }
    currentTime.value = nextTime

    if (currentTime.value >= duration.value) {
      isPlaying.value = false
      return
    }
    schedule()
  }

  /** Move the playhead without touching the play/pause state. */
  function seek(targetTime: number): void {
    const clamped = Math.max(0, Math.min(duration.value, targetTime))
    resetTerminal()
    nextIndex = 0
    for (let i = 0; i < frames.value.length; i += 1) {
      const frame = frames.value[i]
      if (frame.time > clamped) break
      if (frame.type === 'o') writeFrame(frame.data)
      nextIndex = i + 1
    }
    currentTime.value = clamped
    lastFrameTime = nowMs()
  }

  function play(): void {
    if (tornDown || duration.value <= 0) return
    if (currentTime.value >= duration.value) seek(0)
    isPlaying.value = true
    lastFrameTime = nowMs()
    schedule()
  }

  function pause(): void {
    isPlaying.value = false
    stopLoop()
  }

  function toggle(): void {
    if (isPlaying.value) pause()
    else play()
  }

  function restart(): void {
    seek(0)
    play()
  }

  function seekRelative(offsetSeconds: number): void {
    seek(currentTime.value + offsetSeconds)
  }

  function setSpeed(value: number): void {
    const numeric = Number(value)
    if (!Number.isFinite(numeric)) return
    speed.value = Math.min(MAX_REPLAY_SPEED, Math.max(MIN_REPLAY_SPEED, numeric))
  }

  function setEvents(list: readonly ReplayEventLike[]): void {
    events.value = list ?? []
  }

  /** Parse and install a `.cast` payload, resetting the playhead to zero. */
  function loadCast(castText: string): ParsedCast {
    pause()
    const parsed = parseCastRecording(castText)
    header.value = parsed.header
    frames.value = parsed.frames
    duration.value = parsed.duration > 0 ? parsed.duration : resolveFallback()
    currentTime.value = 0
    nextIndex = 0
    resetTerminal()
    return parsed
  }

  /** Clear everything (used when switching recordings). */
  function reset(): void {
    pause()
    frames.value = []
    header.value = null
    events.value = []
    duration.value = 0
    currentTime.value = 0
    nextIndex = 0
    resetTerminal()
  }

  function dispose(): void {
    tornDown = true
    reset()
  }

  if (getCurrentInstance()) onBeforeUnmount(dispose)

  return {
    frames: readonly(frames),
    header: readonly(header),
    events: readonly(events),
    duration: readonly(duration),
    currentTime: readonly(currentTime),
    isPlaying: readonly(isPlaying),
    speed: readonly(speed),
    progress: progress as ComputedRef<number>,
    activeEventIndex,
    loadCast,
    setEvents,
    play,
    pause,
    toggle,
    restart,
    seek,
    seekRelative,
    setSpeed,
    reset,
    dispose,
  }
}
