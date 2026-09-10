import { readonly, ref } from 'vue'

/**
 * Toast service (FE-010).
 *
 * A module-level singleton store plus a `useToast()` composable. Keeping the
 * state outside the component tree means toasts can be raised from anywhere
 * (stores, the API client, router guards) without an active component setup.
 *
 * The public surface mirrors the documented API:
 *   const { push, dismiss, clear } = useToast()
 */
export type ToastVariant = 'info' | 'success' | 'warning' | 'error'

export interface ToastOptions {
  /** Body text shown in the toast. */
  message: string
  /** Semantic variant; defaults to `info`. */
  variant?: ToastVariant
  /** Optional emphasised heading above the message. */
  title?: string
  /**
   * Auto-dismiss delay in milliseconds. `0` keeps the toast until it is
   * dismissed manually. Defaults to `DEFAULT_TOAST_DURATION`.
   */
  duration?: number
}

export interface Toast {
  id: string
  variant: ToastVariant
  title?: string
  message: string
  duration: number
}

export const DEFAULT_TOAST_DURATION = 5000

const VARIANTS: readonly ToastVariant[] = ['info', 'success', 'warning', 'error']

const toasts = ref<Toast[]>([])

interface TimerRecord {
  handle: ReturnType<typeof setTimeout> | null
  remaining: number
  startedAt: number
}

const timers = new Map<string, TimerRecord>()
let counter = 0

function isVariant(value: unknown): value is ToastVariant {
  return typeof value === 'string' && (VARIANTS as readonly string[]).includes(value)
}

function normalise(input: ToastOptions | string, variant?: ToastVariant) {
  if (typeof input === 'string') {
    return {
      message: input,
      variant: isVariant(variant) ? variant : 'info',
      title: undefined as string | undefined,
      duration: DEFAULT_TOAST_DURATION,
    }
  }
  const duration =
    typeof input.duration === 'number' && Number.isFinite(input.duration) && input.duration >= 0
      ? input.duration
      : DEFAULT_TOAST_DURATION
  return {
    message: input.message,
    variant: isVariant(input.variant) ? input.variant : 'info',
    title: input.title,
    duration,
  }
}

function scheduleDismiss(id: string, duration: number): void {
  timers.set(id, {
    handle: setTimeout(() => dismiss(id), duration),
    remaining: duration,
    startedAt: Date.now(),
  })
}

/**
 * Raise a toast. Accepts either `push('message', 'success')` or a full options
 * object. Returns the toast id so callers can dismiss it programmatically.
 */
export function push(input: ToastOptions | string, variant?: ToastVariant): string {
  const options = normalise(input, variant)
  counter += 1
  const id = `toast-${counter}`
  const toast: Toast = {
    id,
    variant: options.variant,
    message: options.message,
    duration: options.duration,
  }
  if (options.title !== undefined) toast.title = options.title

  toasts.value = [...toasts.value, toast]
  if (options.duration > 0) scheduleDismiss(id, options.duration)
  return id
}

/** Remove a single toast (manual dismiss). */
export function dismiss(id: string): void {
  const record = timers.get(id)
  if (record?.handle) clearTimeout(record.handle)
  timers.delete(id)
  toasts.value = toasts.value.filter((toast) => toast.id !== id)
}

/** Remove every toast and cancel all pending auto-dismiss timers. */
export function clear(): void {
  for (const record of timers.values()) {
    if (record.handle) clearTimeout(record.handle)
  }
  timers.clear()
  toasts.value = []
}

/** Suspend a toast's auto-dismiss timer (e.g. while hovered or focused). */
export function pause(id: string): void {
  const record = timers.get(id)
  if (!record || !record.handle) return
  clearTimeout(record.handle)
  record.remaining = Math.max(0, record.remaining - (Date.now() - record.startedAt))
  record.handle = null
}

/** Resume a paused auto-dismiss timer with its remaining time. */
export function resume(id: string): void {
  const record = timers.get(id)
  if (!record || record.handle || record.remaining <= 0) return
  record.startedAt = Date.now()
  record.handle = setTimeout(() => dismiss(id), record.remaining)
}

export function useToast() {
  return {
    toasts: readonly(toasts),
    push,
    dismiss,
    clear,
    pause,
    resume,
  }
}
