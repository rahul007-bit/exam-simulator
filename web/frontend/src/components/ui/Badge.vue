<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useSlots } from 'vue'

import { fallbackCopyText } from '@/composables/useClipboard'

import Icon from '../Icon.vue'
import { FOCUS_RING } from './shared'
import type { BadgeSize, BadgeVariant } from './types'

/**
 * Badge (FE-012) — a small status label. Colours map to the semantic token
 * families (neutral uses surface/border tokens; the rest use the AA-safe
 * `*-text` variants on a 10% tonal fill).
 *
 * Copy support is opt-in (`copyable`): when enabled the badge becomes a real
 * `<button>` that copies `copyText` (or, when omitted, the badge's own slot
 * text) and briefly swaps its `copy` icon for `check`. A neutral copyable badge
 * is rendered with the accent treatment so otherwise-plain chips read as
 * interactive; semantic variants keep their status colour.
 */

const props = withDefaults(
  defineProps<{
    variant?: BadgeVariant
    size?: BadgeSize
    copyable?: boolean
    copyText?: string
    copyLabel?: string
  }>(),
  { variant: 'neutral', size: 'sm', copyable: false, copyText: '', copyLabel: '' },
)

const emit = defineEmits<{ copy: [text: string] }>()

const slots = useSlots()

const VARIANTS: Record<BadgeVariant, string> = {
  neutral: 'border-border bg-hover text-text-muted',
  accent: 'border-accent/40 bg-[var(--color-accent-subtle)] text-accent-text',
  success: 'border-success-text/40 bg-success/10 text-success-text',
  warning: 'border-warning-text/40 bg-warning/10 text-warning-text',
  danger: 'border-danger-text/40 bg-danger/10 text-danger-text',
  info: 'border-info-text/40 bg-info/10 text-info-text',
}

const SIZES: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
}

/** Flatten slot vnodes into their plain text (string/number leaves). */
function flattenText(node: unknown): string {
  if (node === null || node === undefined || typeof node === 'boolean') return ''
  if (typeof node === 'string' || typeof node === 'number') return String(node)
  if (Array.isArray(node)) return node.map(flattenText).join('')
  if (typeof node === 'object' && 'children' in node) {
    return flattenText((node as { children?: unknown }).children)
  }
  return ''
}

const resolvedText = computed(() => props.copyText || flattenText(slots.default?.()))

const effectiveVariant = computed<BadgeVariant>(() =>
  props.copyable && props.variant === 'neutral' ? 'accent' : props.variant,
)

const classes = computed(() => [
  'inline-flex items-center gap-1 rounded-[var(--radius-full)] border font-medium',
  VARIANTS[effectiveVariant.value],
  SIZES[props.size],
])

const interactiveClasses = computed(() => [
  ...classes.value,
  'cursor-pointer transition-opacity hover:opacity-90 active:opacity-80',
  FOCUS_RING,
])

const ariaLabel = computed(() => props.copyLabel || `Copy "${resolvedText.value}"`)

const copied = ref(false)
let resetTimer: ReturnType<typeof setTimeout> | null = null

function scheduleReset(): void {
  if (resetTimer !== null) clearTimeout(resetTimer)
  resetTimer = setTimeout(() => {
    copied.value = false
    resetTimer = null
  }, 1200)
}

function copy(): void {
  const text = resolvedText.value
  emit('copy', text)

  const fallback = (): void => {
    if (typeof document !== 'undefined') fallbackCopyText(text, document)
  }

  if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).catch(fallback)
  } else {
    fallback()
  }

  copied.value = true
  scheduleReset()
}

function onClick(event: MouseEvent): void {
  event.stopPropagation()
  copy()
}

onBeforeUnmount(() => {
  if (resetTimer !== null) clearTimeout(resetTimer)
})
</script>

<template>
  <button
    v-if="copyable"
    type="button"
    :class="interactiveClasses"
    :aria-label="ariaLabel"
    @click="onClick"
    @keydown.stop
  >
    <slot />
    <Icon :name="copied ? 'check' : 'copy'" :size="12" />
  </button>
  <span v-else :class="classes"><slot /></span>
</template>
