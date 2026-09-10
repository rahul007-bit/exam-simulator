import { computed, ref } from 'vue'
import type { CSSProperties, ComputedRef, Ref } from 'vue'

/**
 * useSplitPane (FE-021) — lightweight, dependency-free split-pane model.
 *
 * Drives the candidate workspace: a left (task) pane and a right (desktop /
 * terminal) pane separated by a draggable gutter. The split favours the right
 * pane by default (24% / 76%), clamps both panes to minimum pixel widths, is
 * persisted to `localStorage`, resets on gutter double-click and can collapse
 * the left pane entirely.
 *
 * Design notes:
 *  - No third-party splitter: the ratio is a plain percentage; the min sizes are
 *    enforced in CSS (`min-width`) *and* when converting a pointer position, so
 *    the right pane can never fall below its minimum while dragging.
 *  - SSR / test safe: every `window`/`localStorage`/pointer-capture access is
 *    guarded. `setPointerCapture` is unavailable in jsdom, hence the try/catch.
 *  - Keyboard accessible: the gutter is a `role="separator"`; Arrow keys nudge
 *    the ratio, Home resets and Enter/Space toggles the collapse.
 */

/** Default left-pane share of the workspace width (%). */
export const DEFAULT_SPLIT_RATIO = 24
/** Default minimum width of the left (task) pane, in pixels. */
export const DEFAULT_MIN_LEFT = 300
/** Default minimum width of the right (workspace) pane, in pixels. */
export const DEFAULT_MIN_RIGHT = 520
/** `localStorage` key holding the persisted left-pane ratio. */
export const SPLIT_STORAGE_KEY = 'cka:workspace:split'
/** Percentage moved per ArrowLeft/ArrowRight key press. */
export const DEFAULT_KEYBOARD_STEP = 2
/** Drag the left pane narrower than this (px) to collapse it completely. */
export const DEFAULT_COLLAPSE_THRESHOLD = 96

export interface UseSplitPaneOptions {
  /** The flex container measured to translate pointer X into a ratio. */
  container: Ref<HTMLElement | null>
  /** Initial / reset left-pane share (%). Defaults to {@link DEFAULT_SPLIT_RATIO}. */
  defaultRatio?: number
  /** Left-pane minimum width in px. Defaults to {@link DEFAULT_MIN_LEFT}. */
  minLeft?: number
  /** Right-pane minimum width in px. Defaults to {@link DEFAULT_MIN_RIGHT}. */
  minRight?: number
  /** Persistence key. Defaults to {@link SPLIT_STORAGE_KEY}. */
  storageKey?: string
  /** Percentage step for keyboard nudges. Defaults to {@link DEFAULT_KEYBOARD_STEP}. */
  keyboardStep?: number
  /** Drag narrower than this many px to collapse the left pane. */
  collapseThreshold?: number
}

export interface UseSplitPaneReturn {
  /** Current left-pane share of the workspace (%). */
  ratio: Ref<number>
  /** True while the gutter is being dragged. */
  dragging: Ref<boolean>
  /** True when the left pane is hidden to maximize the workspace. */
  collapsed: Ref<boolean>
  /** Inline style for the left pane (width + min-width). */
  leftStyle: ComputedRef<CSSProperties>
  /** Inline style for the right pane (min-width). */
  rightStyle: ComputedRef<CSSProperties>
  /** `role="separator"` pointerdown handler (starts a drag). */
  onPointerDown: (event: PointerEvent) => void
  /** `role="separator"` keydown handler (arrows / Home / Enter / Space). */
  onKeydown: (event: KeyboardEvent) => void
  /** Move the ratio by `delta` percentage points, clamped to the bounds. */
  nudge: (delta: number) => void
  /** Reset the ratio to the default and persist it. */
  reset: () => void
  /** Toggle the collapsed (workspace-maximized) state. */
  toggleCollapse: () => void
  /** Collapse the left pane. */
  collapse: () => void
  /** Expand the left pane. */
  expand: () => void
  /** Remove any in-flight drag listeners (call from onBeforeUnmount). */
  dispose: () => void
}

function clamp(value: number, min: number, max: number): number {
  if (max < min) return min
  return Math.min(Math.max(value, min), max)
}

function readStoredRatio(key: string, fallback: number): number {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    if (raw == null) return fallback
    const parsed = Number.parseFloat(raw)
    return Number.isFinite(parsed) ? parsed : fallback
  } catch {
    return fallback
  }
}

function persistRatio(key: string, value: number): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(key, String(value))
  } catch {
    /* storage may be unavailable (private mode); the ratio still applies */
  }
}

function readStoredBool(key: string, fallback: boolean): boolean {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    return raw == null ? fallback : raw === '1'
  } catch {
    return fallback
  }
}

function persistBool(key: string, value: boolean): void {
  if (typeof window === 'undefined') return
  try {
    window.localStorage.setItem(key, value ? '1' : '0')
  } catch {
    /* ignore */
  }
}

export function useSplitPane(options: UseSplitPaneOptions): UseSplitPaneReturn {
  const defaultRatio = options.defaultRatio ?? DEFAULT_SPLIT_RATIO
  const minLeft = options.minLeft ?? DEFAULT_MIN_LEFT
  const minRight = options.minRight ?? DEFAULT_MIN_RIGHT
  const storageKey = options.storageKey ?? SPLIT_STORAGE_KEY
  const keyboardStep = options.keyboardStep ?? DEFAULT_KEYBOARD_STEP
  const collapseThreshold = options.collapseThreshold ?? DEFAULT_COLLAPSE_THRESHOLD
  const collapsedKey = `${storageKey}:collapsed`

  const ratio = ref(clamp(readStoredRatio(storageKey, defaultRatio), 0, 100))
  const collapsed = ref(readStoredBool(collapsedKey, false))
  const dragging = ref(false)

  /** Ratio bounds (in %) that keep both panes at or above their min widths. */
  function bounds(width: number): [number, number] {
    if (!width || width <= 0) return [0, 100]
    const lower = clamp((minLeft / width) * 100, 0, 100)
    const upper = clamp(100 - (minRight / width) * 100, 0, 100)
    return [lower, Math.max(lower, upper)]
  }

  function setRatio(value: number, width?: number): void {
    const measured = width ?? options.container.value?.getBoundingClientRect().width ?? 0
    const [lower, upper] = bounds(measured)
    ratio.value = clamp(value, lower, upper)
    persistRatio(storageKey, ratio.value)
  }

  function setRatioFromX(clientX: number, rect: DOMRect): void {
    if (rect.width <= 0) return
    const leftPx = clientX - rect.left
    // Dragging the pane narrower than the threshold snaps it fully closed.
    if (leftPx < collapseThreshold) {
      collapse()
      return
    }
    if (collapsed.value) expand()
    setRatio((leftPx / rect.width) * 100, rect.width)
  }

  function nudge(delta: number): void {
    if (collapsed.value) expand()
    setRatio(ratio.value + delta)
  }

  function reset(): void {
    expand()
    setRatio(defaultRatio)
  }

  function toggleCollapse(): void {
    collapsed.value = !collapsed.value
    persistBool(collapsedKey, collapsed.value)
  }

  function collapse(): void {
    if (collapsed.value) return
    collapsed.value = true
    persistBool(collapsedKey, true)
  }

  function expand(): void {
    if (!collapsed.value) return
    collapsed.value = false
    persistBool(collapsedKey, false)
  }

  let cleanupDrag: (() => void) | null = null

  function onPointerDown(event: PointerEvent): void {
    if (event.button !== 0) return
    const container = options.container.value
    const gutter = event.currentTarget as HTMLElement | null
    if (!container || !gutter) return

    event.preventDefault()
    const rect = container.getBoundingClientRect()
    dragging.value = true

    const onMove = (e: PointerEvent): void => setRatioFromX(e.clientX, rect)
    const onEnd = (e: PointerEvent): void => {
      dragging.value = false
      gutter.removeEventListener('pointermove', onMove)
      gutter.removeEventListener('pointerup', onEnd)
      gutter.removeEventListener('pointercancel', onEnd)
      try {
        if (gutter.hasPointerCapture?.(e.pointerId)) gutter.releasePointerCapture(e.pointerId)
      } catch {
        /* pointer capture unsupported (jsdom) */
      }
      cleanupDrag = null
    }

    try {
      gutter.setPointerCapture?.(event.pointerId)
    } catch {
      /* pointer capture unsupported (jsdom) */
    }
    gutter.addEventListener('pointermove', onMove)
    gutter.addEventListener('pointerup', onEnd)
    gutter.addEventListener('pointercancel', onEnd)

    cleanupDrag = () => {
      gutter.removeEventListener('pointermove', onMove)
      gutter.removeEventListener('pointerup', onEnd)
      gutter.removeEventListener('pointercancel', onEnd)
      dragging.value = false
    }

    setRatioFromX(event.clientX, rect)
  }

  function onKeydown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowLeft':
        event.preventDefault()
        nudge(-keyboardStep)
        break
      case 'ArrowRight':
        event.preventDefault()
        nudge(keyboardStep)
        break
      case 'Home':
        event.preventDefault()
        reset()
        break
      case 'Enter':
      case ' ':
      case 'Spacebar':
        event.preventDefault()
        toggleCollapse()
        break
      default:
        break
    }
  }

  function dispose(): void {
    cleanupDrag?.()
    cleanupDrag = null
  }

  const leftStyle = computed<CSSProperties>(() => ({
    width: `${ratio.value}%`,
    minWidth: `${minLeft}px`,
  }))

  const rightStyle = computed<CSSProperties>(() => ({
    minWidth: `${minRight}px`,
  }))

  return {
    ratio,
    dragging,
    collapsed,
    leftStyle,
    rightStyle,
    onPointerDown,
    onKeydown,
    nudge,
    reset,
    toggleCollapse,
    collapse,
    expand,
    dispose,
  }
}
