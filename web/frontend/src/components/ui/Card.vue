<script setup lang="ts">
import { computed } from 'vue'

import type { CardPadding, CardVariant } from './types'

/**
 * Card (FE-012) — a content surface with optional title/subtitle, header,
 * footer and actions slots. Uses the elevation token scale only (no glows).
 */

const props = withDefaults(
  defineProps<{
    title?: string
    subtitle?: string
    variant?: CardVariant
    padding?: CardPadding
    as?: string
  }>(),
  { variant: 'default', padding: 'md', as: 'section' },
)

const VARIANTS: Record<CardVariant, string> = {
  default: 'border border-border bg-surface',
  outlined: 'border border-border-strong bg-transparent',
  elevated: 'border border-border bg-elevated shadow-[var(--shadow-sm)]',
}

const PADDING: Record<CardPadding, string> = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

const classes = computed(() => [
  'rounded-[var(--radius-lg)] text-text',
  VARIANTS[props.variant],
])
</script>

<template>
  <component :is="as" :class="classes">
    <header
      v-if="title || subtitle || $slots.header || $slots.actions"
      class="flex items-start justify-between gap-3 border-b border-border px-4 py-3"
    >
      <div class="min-w-0">
        <slot name="header">
          <h3 v-if="title" class="m-0 truncate text-base font-semibold text-text">{{ title }}</h3>
          <p v-if="subtitle" class="m-0 mt-0.5 text-sm text-text-muted">{{ subtitle }}</p>
        </slot>
      </div>
      <div v-if="$slots.actions" class="flex flex-none items-center gap-2">
        <slot name="actions" />
      </div>
    </header>
    <div :class="PADDING[padding]">
      <slot />
    </div>
    <footer
      v-if="$slots.footer"
      class="border-t border-border px-4 py-3 text-sm text-text-muted"
    >
      <slot name="footer" />
    </footer>
  </component>
</template>
