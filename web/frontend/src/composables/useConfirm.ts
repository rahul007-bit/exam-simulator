import { computed, readonly, shallowRef } from 'vue'

/**
 * Promise-based confirm + prompt service (FE-011).
 *
 * A module-level singleton, mirroring `useToast` (FE-010): dialogs can be
 * raised from anywhere (stores, the API client, router guards) without an
 * active component setup. A single host component (`<ConfirmDialog/>`, mounted
 * once in `App.vue`) renders the active request with Headless UI's `Dialog`.
 *
 * Usage:
 *   const ok = await confirm({ title: 'Delete preset', danger: true })
 *   const name = await prompt({ title: 'Session name', defaultValue: 'lab-1' })
 *
 * Concurrency policy: requests are **queued (FIFO)**. Exactly one dialog is
 * visible at a time; further concurrent calls wait until the active dialog
 * settles, then appear in the order they were made. This is deterministic and
 * avoids losing/rejecting promises or stacking dialogs. Callers that must not
 * block should check `active` or simply await their own promise.
 */

export interface ConfirmOptions {
  /** Heading shown in the dialog. Defaults to "Confirm action". */
  title?: string
  /** Body copy describing what is being confirmed. */
  message?: string
  /** Label for the affirmative button. Defaults to "OK". */
  confirmLabel?: string
  /** Label for the dismissive button. Defaults to "Cancel". */
  cancelLabel?: string
  /** Render the affirmative button with the semantic `danger` treatment. */
  danger?: boolean
}

export interface PromptOptions extends ConfirmOptions {
  /** Placeholder shown while the input is empty. */
  placeholder?: string
  /** Value the input is pre-filled with when the prompt opens. */
  defaultValue?: string
}

export type DialogKind = 'confirm' | 'prompt'

/** Normalised, resolved shape consumed by the host component. */
export interface DialogRequest {
  id: number
  kind: DialogKind
  title: string
  message: string
  confirmLabel: string
  cancelLabel: string
  danger: boolean
  placeholder: string
  defaultValue: string
}

type DialogValue = boolean | string | null

interface PendingRequest {
  request: DialogRequest
  resolve: (value: DialogValue) => void
}

const DEFAULT_CONFIRM_LABEL = 'OK'
const DEFAULT_CANCEL_LABEL = 'Cancel'

let counter = 0

const pending = shallowRef<PendingRequest[]>([])

/** The dialog currently displayed, or `null` when the queue is empty. */
const active = computed<DialogRequest | null>(() => pending.value[0]?.request ?? null)

function normalise(kind: DialogKind, options: ConfirmOptions | PromptOptions): DialogRequest {
  const prompt = kind === 'prompt' ? (options as PromptOptions) : undefined
  counter += 1
  return {
    id: counter,
    kind,
    title: options.title ?? (kind === 'prompt' ? 'Enter a value' : 'Confirm action'),
    message: options.message ?? '',
    confirmLabel: options.confirmLabel ?? DEFAULT_CONFIRM_LABEL,
    cancelLabel: options.cancelLabel ?? DEFAULT_CANCEL_LABEL,
    danger: options.danger ?? false,
    placeholder: prompt?.placeholder ?? '',
    defaultValue: prompt?.defaultValue ?? '',
  }
}

function enqueue(kind: DialogKind, options: ConfirmOptions | PromptOptions): Promise<DialogValue> {
  return new Promise<DialogValue>((resolve) => {
    pending.value = [...pending.value, { request: normalise(kind, options), resolve }]
  })
}

/**
 * Show a confirmation dialog. Resolves `true` when the affirmative button is
 * activated, `false` on cancel / `Escape` / backdrop click.
 */
export function confirm(options: ConfirmOptions = {}): Promise<boolean> {
  return enqueue('confirm', options) as Promise<boolean>
}

/**
 * Show a prompt dialog. Resolves the submitted string when the affirmative
 * button (or `Enter`) is activated, `null` on cancel / `Escape` / backdrop click.
 */
export function prompt(options: PromptOptions = {}): Promise<string | null> {
  return enqueue('prompt', options) as Promise<string | null>
}

/**
 * Resolve the active dialog with its affirmative action: `confirm()` resolves
 * `true`; `prompt()` resolves the submitted `value` (defaulting to `''`).
 */
export function accept(value = ''): void {
  const head = pending.value[0]
  if (!head) return
  const { request, resolve } = head
  pending.value = pending.value.slice(1)
  resolve(request.kind === 'prompt' ? value : true)
}

/**
 * Resolve the active dialog with its dismissive action: `confirm()` resolves
 * `false`; `prompt()` resolves `null`.
 */
export function cancel(): void {
  const head = pending.value[0]
  if (!head) return
  const { request, resolve } = head
  pending.value = pending.value.slice(1)
  resolve(request.kind === 'prompt' ? null : false)
}

export function useConfirm() {
  return {
    active: readonly(active),
    confirm,
    prompt,
    accept,
    cancel,
  }
}
