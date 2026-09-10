<script setup lang="ts">
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from '@headlessui/vue'
import { computed } from 'vue'

import { FOCUS_RING } from './shared'
import type { SegmentOption } from './types'

/**
 * SegmentedControl (FE-012) — Headless UI `RadioGroup` rendered as a single
 * selectable track. Headless UI owns the `radiogroup`/`radio` roles, roving
 * focus and arrow-key navigation; this component styles the track and options.
 */

const props = withDefaults(
  defineProps<{
    modelValue?: string
    options: SegmentOption[]
    label?: string
    disabled?: boolean
    size?: 'sm' | 'md'
  }>(),
  { modelValue: '', disabled: false, size: 'md' },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const SIZES = {
  sm: 'h-7 px-3 text-xs',
  md: 'h-8 px-3.5 text-sm',
} as const

const sizeClass = computed(() => SIZES[props.size])

function update(value: string): void {
  emit('update:modelValue', value)
}
</script>

<template>
  <RadioGroup
    :model-value="modelValue"
    :disabled="disabled"
    class="flex flex-col items-start gap-1.5"
    @update:model-value="update"
  >
    <RadioGroupLabel v-if="label" class="text-sm font-medium text-text">{{ label }}</RadioGroupLabel>
    <div
      class="inline-flex items-center gap-0.5 rounded-[var(--radius-md)] border border-border bg-surface p-0.5"
    >
      <RadioGroupOption
        v-for="option in options"
        :key="option.value"
        v-slot="{ checked, disabled: optionDisabled }"
        as="template"
        :value="option.value"
        :disabled="option.disabled"
      >
        <button
          type="button"
          :class="[
            'inline-flex items-center justify-center rounded-[var(--radius-sm)] font-medium transition-colors',
            sizeClass,
            checked
              ? 'bg-accent-solid text-accent-contrast'
              : 'text-text-muted hover:bg-hover hover:text-text',
            optionDisabled ? 'cursor-not-allowed opacity-60' : '',
            FOCUS_RING,
          ]"
        >
          {{ option.label }}
        </button>
      </RadioGroupOption>
    </div>
  </RadioGroup>
</template>
