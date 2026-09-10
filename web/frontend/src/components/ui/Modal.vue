<script setup lang="ts">
import {
  Dialog,
  DialogDescription,
  DialogPanel,
  DialogTitle,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import { computed, useSlots } from 'vue'

import type { ModalSize } from './types'

/**
 * Modal (FE-012) — accessible dialog built on Headless UI `Dialog`. Provides the
 * focus trap, `Escape` to close, `role="dialog"` + `aria-modal="true"` and the
 * `aria-labelledby` / `aria-describedby` wiring. A visually hidden title is
 * always rendered so the dialog is never unnamed.
 */

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    description?: string
    size?: ModalSize
  }>(),
  { size: 'md' },
)

const emit = defineEmits<{ 'update:modelValue': [value: boolean]; close: [] }>()

const slots = useSlots()
const hasTitle = computed(() => Boolean(props.title) || Boolean(slots.title))

const SIZES: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-6xl',
}

function close(): void {
  emit('update:modelValue', false)
  emit('close')
}
</script>

<template>
  <TransitionRoot appear :show="modelValue" as="template">
    <Dialog data-testid="modal" class="relative z-[1000]" @close="close">
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
            leave="duration-100 ease-in motion-reduce:transition-none"
            leave-from="opacity-100 translate-y-0"
            leave-to="opacity-0 translate-y-1"
          >
            <DialogPanel
              data-testid="modal-panel"
              :class="[
                'w-full rounded-[var(--radius-lg)] border border-border bg-elevated p-4 text-text shadow-[var(--shadow-lg)]',
                SIZES[size],
              ]"
            >
              <DialogTitle :class="hasTitle ? 'm-0 text-base font-semibold text-text' : 'sr-only'">
                <slot name="title">{{ title || 'Dialog' }}</slot>
              </DialogTitle>
              <DialogDescription
                v-if="description"
                class="m-0 mt-1 text-sm leading-normal text-text-muted"
              >
                {{ description }}
              </DialogDescription>

              <div class="mt-3">
                <slot />
              </div>

              <div v-if="$slots.footer" class="mt-3 flex flex-row-reverse gap-2">
                <slot name="footer" />
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
