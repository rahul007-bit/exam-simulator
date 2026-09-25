<script setup lang="ts">
import { computed } from 'vue'

import Icon from '../Icon.vue'

/**
 * Spinner (FE-012, FE-014) — the loading glyph rendered through `Icon`.
 *
 * `decorative` renders a bare, `aria-hidden` glyph for use inside a control
 * (e.g. a loading Button that already exposes `aria-busy`). The default renders
 * an accessible `role="status"` region with a visually hidden label.
 */
type SpinnerSize = 'sm' | 'md' | 'lg'

const props = withDefaults(
  defineProps<{
    size?: SpinnerSize
    /** Visually hidden announcement; only used when not `decorative`. */
    label?: string
    /** When true the spinner is presentational (caller owns the status). */
    decorative?: boolean
  }>(),
  { size: 'md', label: 'Loading', decorative: false },
)

const SIZES: Record<SpinnerSize, number> = {
  sm: 16,
  md: 20,
  lg: 32,
}

const dimension = computed(() => SIZES[props.size])
const iconClass = 'animate-spin motion-reduce:animate-none'
</script>

<template>
  <span v-if="!decorative" role="status" class="inline-flex items-center gap-2 text-text-muted">
    <Icon name="spinner" :size="dimension" :class="iconClass" />
    <span class="sr-only">{{ label }}</span>
  </span>

  <Icon v-else name="spinner" :size="dimension" :class="iconClass" />
</template>
