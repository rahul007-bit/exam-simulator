<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { Button, Card, Icon, Select } from '@/components/ui'
import type { SelectOption } from '@/components/ui'

/**
 * AdminConfigForm (FE-032) — the global default-preset selector.
 *
 * Presentational: the persisted value arrives via `saved` (loaded from
 * `GET /api/admin/config`) and the chosen value is emitted through `save`. A
 * local draft keeps the control responsive while marking the form dirty, so the
 * Save action stays disabled until the selection actually changes.
 */

const props = withDefaults(
  defineProps<{
    /** Persisted default preset filename, e.g. `mock-01-acme` or `all`. */
    saved: string
    options: SelectOption[]
    loading?: boolean
    saving?: boolean
    disabled?: boolean
  }>(),
  { loading: false, saving: false, disabled: false },
)

const emit = defineEmits<{
  save: [preset: string]
  reload: []
}>()

const draft = ref(props.saved)

watch(
  () => props.saved,
  (value) => {
    draft.value = value
  },
)

const dirty = computed(() => draft.value !== props.saved)
const busy = computed(() => props.loading || props.saving || props.disabled)
const activeLabel = computed(
  () => props.options.find((option) => option.value === draft.value)?.label ?? draft.value,
)

function onSubmit(): void {
  if (!dirty.value || busy.value) return
  emit('save', draft.value)
}
</script>

<template>
  <Card title="Default preset" subtitle="Exam preset that new candidate sessions start with.">
    <template #actions>
      <Button
        variant="secondary"
        size="sm"
        :loading="loading"
        :disabled="loading || saving"
        data-testid="config-refresh"
        @click="emit('reload')"
      >
        <Icon name="refresh" :size="16" class="flex-none" />
        Refresh
      </Button>
    </template>

    <form class="flex flex-col gap-3" novalidate @submit.prevent="onSubmit">
      <Select
        :model-value="draft"
        :options="options"
        label="Preset"
        placeholder="Select a preset"
        :disabled="busy"
        @update:model-value="draft = $event"
      />

      <p class="m-0 text-xs text-text-muted">
        Active default: <span class="font-medium text-text">{{ activeLabel }}</span>
      </p>

      <div class="flex justify-end">
        <Button
          type="submit"
          variant="primary"
          :loading="saving"
          :disabled="!dirty || busy"
          data-testid="config-save"
        >
          Save default preset
        </Button>
      </div>
    </form>
  </Card>
</template>
