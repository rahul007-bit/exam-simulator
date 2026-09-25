<script setup lang="ts">
import { computed } from 'vue'

import Spinner from './Spinner.vue'
import { DISABLED, FOCUS_RING } from './shared'
import type { ButtonSize, ButtonVariant } from './types'

/**
 * Button (FE-012) — primary / secondary / ghost / danger variants, three sizes,
 * disabled and loading states. Colours come from tokens only (D-003): the
 * primary fill uses `accent-solid` (AA-safe with white text), danger uses the
 * AA-safe `danger-text` tonal treatment.
 */

const props = withDefaults(
  defineProps<{
    variant?: ButtonVariant
    size?: ButtonSize
    type?: 'button' | 'submit' | 'reset'
    disabled?: boolean
    loading?: boolean
    block?: boolean
  }>(),
  { variant: 'secondary', size: 'md', type: 'button', disabled: false, loading: false, block: false },
)

const VARIANTS: Record<ButtonVariant, string> = {
  primary:
    'border border-transparent bg-accent-solid text-accent-contrast hover:bg-accent-solid-hover',
  secondary: 'border border-border bg-surface text-text hover:bg-hover',
  ghost: 'border border-transparent bg-transparent text-text hover:bg-hover',
  warning: 'border border-warning-text/40 bg-warning/10 text-warning-text hover:bg-warning/20',
  danger: 'border border-danger-text/40 bg-danger/10 text-danger-text hover:bg-danger/20',
}

const SIZES: Record<ButtonSize, string> = {
  sm: 'h-8 gap-1.5 px-3 text-xs',
  md: 'h-9 gap-2 px-4 text-sm',
  lg: 'h-11 gap-2 px-5 text-base',
}

const classes = computed(() => [
  'inline-flex select-none items-center justify-center rounded-[var(--radius-sm)] font-semibold transition-colors',
  VARIANTS[props.variant],
  SIZES[props.size],
  props.block ? 'w-full' : '',
  FOCUS_RING,
  DISABLED,
])
</script>

<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading ? 'true' : undefined"
    :class="classes"
  >
    <Spinner v-if="loading" size="sm" decorative />
    <slot />
  </button>
</template>
