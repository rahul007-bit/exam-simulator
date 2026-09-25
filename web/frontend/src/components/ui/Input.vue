<script setup lang="ts">
import { computed, useId } from 'vue'

import { DISABLED, FOCUS_RING } from './shared'

/**
 * Input (FE-012) — label, hint and error wiring included. The label's `for`
 * matches the generated input id; `error` sets `aria-invalid` and points
 * `aria-describedby` at the message so assistive tech announces it.
 */
const props = withDefaults(
  defineProps<{
    modelValue?: string | number
    label?: string
    type?: string
    placeholder?: string
    name?: string
    autocomplete?: string
    disabled?: boolean
    readonly?: boolean
    required?: boolean
    error?: string
    hint?: string
    id?: string
  }>(),
  { modelValue: '', type: 'text', disabled: false, readonly: false, required: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const uid = useId()
const inputId = computed(() => props.id ?? `input-${uid}`)
const errorId = computed(() => `${inputId.value}-error`)
const hintId = computed(() => `${inputId.value}-hint`)

const describedBy = computed(() => {
  const ids = []
  if (props.hint) ids.push(hintId.value)
  if (props.error) ids.push(errorId.value)
  return ids.length ? ids.join(' ') : undefined
})

const classes = computed(() => [
  'h-9 w-full rounded-[var(--radius-sm)] border bg-surface px-3 text-sm text-text transition-colors placeholder:text-text-muted',
  props.error ? 'border-danger-text' : 'border-border hover:border-border-strong',
  FOCUS_RING,
  DISABLED,
])

function onInput(event: Event): void {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="inputId" class="text-sm font-medium text-text">
      {{ label }}
      <span v-if="required" aria-hidden="true" class="text-danger-text">*</span>
      <span v-if="required" class="sr-only">(required)</span>
    </label>
    <input
      :id="inputId"
      :name="name"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :disabled="disabled"
      :readonly="readonly"
      :required="required"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="describedBy"
      :class="classes"
      @input="onInput"
    />
    <p v-if="error" :id="errorId" class="text-xs text-danger-text">{{ error }}</p>
    <p v-else-if="hint" :id="hintId" class="text-xs text-text-muted">{{ hint }}</p>
  </div>
</template>
