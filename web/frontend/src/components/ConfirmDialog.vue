<script setup lang="ts">
import {
  Dialog,
  DialogDescription,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import { computed, nextTick, ref, watch } from 'vue'

import { useConfirm } from '@/composables/useConfirm'
import type { DialogRequest } from '@/composables/useConfirm'

/**
 * Single dialog host for `useConfirm` (FE-011).
 *
 * Mounted exactly once in `App.vue`. Focus trap, `Escape` to close,
 * `role="dialog"`, `aria-modal="true"` and the `aria-labelledby` /
 * `aria-describedby` wiring come from Headless UI's `Dialog`. This component
 * supplies content, styling and the bridge back into the promise queue.
 */
const { active, accept, cancel } = useConfirm()

const EMPTY_REQUEST: DialogRequest = {
  id: 0,
  kind: 'confirm',
  title: '',
  message: '',
  confirmLabel: 'OK',
  cancelLabel: 'Cancel',
  danger: false,
  placeholder: '',
  defaultValue: '',
}

const dialog = computed<DialogRequest>(() => active.value ?? EMPTY_REQUEST)
const isOpen = computed(() => active.value !== null)
const isPrompt = computed(() => dialog.value.kind === 'prompt')
const description = computed(
  () =>
    dialog.value.message ||
    (isPrompt.value
      ? 'Type a value, then confirm or cancel.'
      : 'This action requires confirmation.'),
)

const inputValue = ref('')

// Remember the element that opened the dialog so focus can be returned to it on
// close. Headless UI restores focus too, but this runs after its unmount cleanup
// and guarantees the invoker (which may sit outside the dialog's inert tree)
// regains focus deterministically.
let invoker: HTMLElement | null = null
watch(isOpen, async (open, wasOpen) => {
  if (open && !wasOpen) {
    const focused = document.activeElement
    invoker = focused instanceof HTMLElement && focused !== document.body ? focused : null
    return
  }
  if (!open && wasOpen) {
    await nextTick()
    if (invoker?.isConnected) invoker.focus()
    invoker = null
  }
})

// Pre-fill the input for each new prompt request (and clear it for confirms).
watch(
  () => active.value?.id,
  () => {
    const request = active.value
    inputValue.value = request?.kind === 'prompt' ? request.defaultValue : ''
  },
)

const CONFIRM_BASE =
  'inline-flex items-center justify-center rounded-[var(--radius-sm)] border px-4 py-2 text-sm font-semibold transition-colors'
const CONFIRM_ACCENT =
  'border-transparent bg-accent-solid text-accent-contrast hover:bg-accent-solid-hover'
const CONFIRM_DANGER =
  'border-danger-text/40 bg-danger/10 text-danger-text hover:bg-danger/20'
const CANCEL_BASE =
  'inline-flex items-center justify-center rounded-[var(--radius-sm)] border border-border bg-transparent px-4 py-2 text-sm font-medium text-text transition-colors hover:bg-hover'

function submit(): void {
  accept(isPrompt.value ? inputValue.value : '')
}
</script>

<template>
  <TransitionRoot v-if="isOpen" :key="dialog.id" appear :show="true" as="template">
    <Dialog data-testid="dialog-root" class="relative z-[1000]" @close="() => cancel()">
      <TransitionChild
        as="template"
        enter="duration-150 ease-out motion-reduce:transition-none"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-100 ease-in motion-reduce:transition-none"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/50" aria-hidden="true" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="duration-150 ease-out motion-reduce:transition-none"
            enter-from="opacity-0 translate-y-1"
            enter-to="opacity-100 translate-y-0"
          >
            <DialogPanel
              data-testid="dialog-panel"
              class="w-full max-w-md rounded-[var(--radius-lg)] border border-border bg-elevated p-4 text-text shadow-[var(--shadow-lg)]"
            >
              <DialogTitle class="m-0 mb-1.5 text-base font-semibold text-text">
                {{ dialog.title }}
              </DialogTitle>
              <DialogDescription
                class="m-0 mb-3 text-sm leading-normal text-text-muted"
                :class="{ 'sr-only': !dialog.message }"
              >
                {{ description }}
              </DialogDescription>

              <input
                v-if="isPrompt"
                v-model="inputValue"
                data-testid="prompt-input"
                type="text"
                class="mb-3 w-full rounded-[var(--radius-sm)] border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted"
                :placeholder="dialog.placeholder || undefined"
                @keydown.enter.prevent="submit"
              />

              <div class="flex flex-row-reverse gap-2">
                <button
                  type="button"
                  data-testid="confirm"
                  :class="[CONFIRM_BASE, dialog.danger ? CONFIRM_DANGER : CONFIRM_ACCENT]"
                  @click="submit"
                >
                  {{ dialog.confirmLabel }}
                </button>
                <button
                  type="button"
                  data-testid="cancel"
                  :class="CANCEL_BASE"
                  @click="cancel()"
                >
                  {{ dialog.cancelLabel }}
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
