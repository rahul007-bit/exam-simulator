<script setup lang="ts">
import { computed } from 'vue'

import { ICONS } from './ui/icons'
import type { IconName, IconShape } from './ui/icons'

/**
 * Icon (FE-014) — the single inline-SVG renderer for the UI.
 *
 * Consumes the typed catalogue in `./ui/icons.ts` and renders stroke-based,
 * `currentColor` glyphs. By default the SVG is presentational (`aria-hidden`);
 * pass `label` only when the icon is the sole accessible name for a control
 * (otherwise the surrounding button/link supplies the label).
 *
 * Size defaults to 16px and accepts a number (px) or any CSS length string.
 */
defineOptions({ name: 'UiIcon' })

const props = withDefaults(
  defineProps<{
    name: IconName
    size?: number | string
    strokeWidth?: number
    /** Accessible name; when set the SVG becomes `role="img"`. */
    label?: string
  }>(),
  { size: 16, strokeWidth: 2, label: '' },
)

const shapes = computed<readonly IconShape[]>(() => ICONS[props.name])
const dimension = computed(() =>
  typeof props.size === 'number' ? `${props.size}px` : props.size,
)
const a11y = computed(() =>
  props.label
    ? { role: 'img' as const, 'aria-label': props.label }
    : { 'aria-hidden': 'true' as const },
)
</script>

<template>
  <svg
    viewBox="0 0 24 24"
    :width="dimension"
    :height="dimension"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    focusable="false"
    v-bind="a11y"
  >
    <template v-for="(shape, index) in shapes" :key="index">
      <circle
        v-if="shape.tag === 'circle'"
        :cx="shape.cx"
        :cy="shape.cy"
        :r="shape.r"
        :class="shape.class"
      />
      <path v-else :d="shape.d" :class="shape.class" />
    </template>
  </svg>
</template>
