<script setup lang="ts">
import { computed } from 'vue'

import Icon from '../Icon.vue'
import { FOCUS_RING } from './shared'
import type { ChipVariant } from './types'

/**
 * Chip (FE-012) — like Badge but optionally dismissible. The remove control is a
 * real, labelled `<button>` with a token focus ring, so keyboard users can reach
 * and activate it.
 */

const props = withDefaults(
  defineProps<{
    variant?: ChipVariant
    removable?: boolean
    disabled?: boolean
    removeLabel?: string
  }>(),
  { variant: 'neutral', removable: false, disabled: false, removeLabel: 'Remove' },
)

const emit = defineEmits<{ remove: [] }>()

const VARIANTS: Record<ChipVariant, string> = {
  neutral: 'border-border bg-hover text-text',
  accent: 'border-accent/40 bg-[var(--color-accent-subtle)] text-accent-text',
  success: 'border-success-text/40 bg-success/10 text-success-text',
  warning: 'border-warning-text/40 bg-warning/10 text-warning-text',
  danger: 'border-danger-text/40 bg-danger/10 text-danger-text',
  info: 'border-info-text/40 bg-info/10 text-info-text',
}

const classes = computed(() => [
  'inline-flex items-center gap-1 rounded-[var(--radius-full)] border py-0.5 text-sm font-medium',
  props.removable ? 'pl-2.5 pr-1' : 'px-2.5',
  VARIANTS[props.variant],
])
</script>

<template>
  <span :class="classes">
    <slot />
    <button
      v-if="removable"
      type="button"
      :disabled="disabled"
      :aria-label="removeLabel"
      :class="[
        'inline-flex h-4 w-4 flex-none items-center justify-center rounded-[var(--radius-full)] border border-transparent bg-transparent p-0 text-current transition-colors hover:bg-black/10 disabled:cursor-not-allowed disabled:opacity-60',
        FOCUS_RING,
      ]"
      @click="emit('remove')"
    >
      <Icon name="close" :size="10" :stroke-width="3" />
    </button>
  </span>
</template>
