<script setup lang="ts">
import { TransitionRoot } from '@headlessui/vue'

import Icon from '@/components/Icon.vue'
import { useToast } from '@/composables/useToast'
import type { ToastVariant } from '@/composables/useToast'

const { toasts, dismiss, pause, resume } = useToast()

/**
 * Variant → semantic token utility classes (D-002). These resolve to the
 * `--color-*-text` AA-safe text variants declared in tokens.css via the
 * `@theme inline` mapping in base.css. No raw colours here (FE-002).
 */
const ACCENT_BORDER: Record<ToastVariant, string> = {
  info: 'border-l-info-text',
  success: 'border-l-success-text',
  warning: 'border-l-warning-text',
  error: 'border-l-danger-text',
}

const ACCENT_TEXT: Record<ToastVariant, string> = {
  info: 'text-info-text',
  success: 'text-success-text',
  warning: 'text-warning-text',
  error: 'text-danger-text',
}
</script>

<template>
  <div class="toaster fixed top-4 right-4 z-[1000] w-[min(24rem,calc(100vw-var(--space-8)))] pointer-events-none" role="region" aria-label="Notifications">
    <div
      class="toaster__list m-0 flex list-none flex-col gap-2 p-0"
      aria-live="polite"
      aria-relevant="additions removals"
    >
      <!--
        Headless UI owns the accessible enter transition (replaces the old
        scoped `toast-in` keyframes). Each toast mounts with `:show="true"` and
        `appear`, so it animates in without changing the dismiss lifecycle.
      -->
      <TransitionRoot
        v-for="toast in toasts"
        :key="toast.id"
        :show="true"
        appear
        as="div"
        class="toast pointer-events-auto flex items-start gap-2 p-3 text-text bg-elevated border border-border border-l-[3px] rounded-[var(--radius-md)] shadow-[var(--shadow-md)]"
        :class="[`toast--${toast.variant}`, ACCENT_BORDER[toast.variant]]"
        :role="toast.variant === 'error' ? 'alert' : 'status'"
        enter="transition duration-150 ease-out motion-reduce:transition-none"
        enter-from="opacity-0 -translate-y-1"
        enter-to="opacity-100 translate-y-0"
        @mouseenter="pause(toast.id)"
        @mouseleave="resume(toast.id)"
        @focusin="pause(toast.id)"
        @focusout="resume(toast.id)"
      >
        <span class="toast__icon mt-px inline-flex flex-none" :class="ACCENT_TEXT[toast.variant]" aria-hidden="true">
          <Icon :name="toast.variant" :size="18" />
        </span>

        <div class="toast__content min-w-0 flex-auto">
          <p v-if="toast.title" class="toast__title m-0 mb-1 text-sm font-semibold text-text">
            {{ toast.title }}
          </p>
          <p class="toast__message m-0 text-sm leading-normal [overflow-wrap:anywhere] text-text">
            {{ toast.message }}
          </p>
        </div>

        <button
          type="button"
          class="toast__close inline-flex h-6 w-6 flex-none cursor-pointer items-center justify-center rounded-[var(--radius-sm)] border border-transparent bg-transparent p-0 text-text-muted transition-colors hover:bg-hover hover:text-text"
          :aria-label="`Dismiss ${toast.variant} notification`"
          @click="dismiss(toast.id)"
        >
          <Icon name="close" :size="14" />
        </button>
      </TransitionRoot>
    </div>
  </div>
</template>
