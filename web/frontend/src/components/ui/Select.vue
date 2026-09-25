<script setup lang="ts">
import {
  Listbox,
  ListboxButton,
  ListboxLabel,
  ListboxOption,
  ListboxOptions,
  TransitionRoot,
} from '@headlessui/vue'
import { computed, useId } from 'vue'

import Icon from '../Icon.vue'
import { FOCUS_RING } from './shared'
import type { SelectOption } from './types'

/**
 * Select (FE-012) — Headless UI `Listbox`. Headless UI owns the combobox
 * semantics, keyboard interaction (arrows / Home / End / typeahead) and the
 * `aria-activedescendant` wiring; this component supplies token styling and a
 * typed option list.
 *
 * Fallthrough attributes (e.g. `aria-label`) are bound to the `ListboxButton`
 * rather than the Headless UI root: `Listbox` renders a `template`, and passing
 * props through a template throws ("Passing props on template!").
 */

defineOptions({ inheritAttrs: false })

const props = withDefaults(
  defineProps<{
    modelValue?: string
    options: SelectOption[]
    label?: string
    placeholder?: string
    disabled?: boolean
    id?: string
  }>(),
  { modelValue: '', placeholder: 'Select an option', disabled: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const uid = useId()
const buttonId = computed(() => props.id ?? `select-${uid}`)
const selected = computed(() => props.options.find((option) => option.value === props.modelValue))

function update(value: string): void {
  emit('update:modelValue', value)
}
</script>

<template>
  <Listbox :model-value="modelValue" :disabled="disabled" @update:model-value="update">
    <ListboxLabel v-if="label" class="mb-1.5 block text-sm font-medium text-text">
      {{ label }}
    </ListboxLabel>
    <div class="relative">
      <ListboxButton
        :id="buttonId"
        v-bind="$attrs"
        :class="[
          'flex h-9 w-full items-center justify-between gap-2 rounded-[var(--radius-sm)] border bg-surface px-3 text-left text-sm transition-colors',
          disabled ? 'cursor-not-allowed opacity-60' : 'border-border hover:border-border-strong',
          FOCUS_RING,
        ]"
      >
        <span :class="selected ? 'truncate text-text' : 'truncate text-text-muted'">
          {{ selected ? selected.label : placeholder }}
        </span>
        <Icon name="chevron-down" :size="16" class="flex-none text-text-muted" />
      </ListboxButton>

      <TransitionRoot
        as="template"
        enter="transition duration-100 ease-out motion-reduce:transition-none"
        enter-from="opacity-0 -translate-y-1"
        enter-to="opacity-100 translate-y-0"
        leave="transition duration-75 ease-in motion-reduce:transition-none"
        leave-from="opacity-100 translate-y-0"
        leave-to="opacity-0 -translate-y-1"
      >
        <ListboxOptions
          class="focus:outline-none absolute z-50 mt-1 max-h-60 w-full overflow-auto rounded-[var(--radius-md)] border border-border bg-elevated p-1 text-sm shadow-[var(--shadow-md)]"
        >
          <ListboxOption
            v-for="option in options"
            :key="option.value"
            v-slot="{ active, selected: isSelected }"
            as="template"
            :value="option.value"
            :disabled="option.disabled"
          >
            <li
              :class="[
                'flex cursor-pointer items-center justify-between gap-2 rounded-[var(--radius-sm)] px-2.5 py-1.5',
                active ? 'bg-hover text-text' : 'text-text',
                isSelected ? 'font-medium text-accent-text' : '',
                option.disabled ? 'cursor-not-allowed opacity-60' : '',
              ]"
            >
              <span class="truncate">{{ option.label }}</span>
              <Icon v-if="isSelected" name="check" :size="14" :stroke-width="2.5" class="flex-none" />
            </li>
          </ListboxOption>
        </ListboxOptions>
      </TransitionRoot>
    </div>
  </Listbox>
</template>
