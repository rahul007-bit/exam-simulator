<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import type { ResourceInfo } from '@/api/admin'
import { Badge, Button, Card, Icon, Input } from '@/components/ui'
import type { BadgeVariant } from '@/components/ui'
import { formatMemMb, validateMaxSessions } from '@/composables/useAdminConfig'

/**
 * AdminResourceForm (FE-032) — server capacity snapshot plus the max concurrent
 * sessions edit.
 *
 * Presentational: `resources` carries the `GET /api/admin/resources` snapshot;
 * valid submissions are emitted through `save`, invalid ones through `invalid`
 * (so the parent can raise a toast) while the field itself shows the inline
 * error. The draft only resyncs from the server when the user has no unsaved
 * edit in flight.
 */

const props = withDefaults(
  defineProps<{
    resources: ResourceInfo | null
    loading?: boolean
    saving?: boolean
    disabled?: boolean
  }>(),
  { loading: false, saving: false, disabled: false },
)

const emit = defineEmits<{
  save: [limit: number]
  invalid: [message: string]
  reload: []
}>()

const draft = ref('')
const error = ref<string | null>(null)

const persisted = computed(() => props.resources?.max_concurrent_sessions ?? null)
const dirty = computed(
  () => persisted.value !== null && draft.value !== String(persisted.value),
)
const busy = computed(() => props.loading || props.saving || props.disabled)

watch(
  persisted,
  (value) => {
    if (value !== null && !dirty.value) draft.value = String(value)
  },
  { immediate: true },
)

const capacity = computed(() => {
  const info = props.resources
  if (!info) return { variant: 'neutral' as BadgeVariant, label: 'Unknown' }
  if (info.can_start) return { variant: 'success' as BadgeVariant, label: 'Optimal' }
  if (info.running_containers >= info.max_concurrent_sessions) {
    return { variant: 'danger' as BadgeVariant, label: 'At capacity' }
  }
  return { variant: 'warning' as BadgeVariant, label: 'Low memory' }
})

const slots = computed(() => {
  const info = props.resources
  if (!info) return null
  return info.max_concurrent_sessions - info.running_containers
})

function onSubmit(): void {
  if (busy.value) return
  const parsed = Number(draft.value)
  const invalid = validateMaxSessions(parsed)
  if (invalid) {
    error.value = invalid
    emit('invalid', invalid)
    return
  }
  error.value = null
  emit('save', parsed)
}
</script>

<template>
  <Card
    title="Server resources"
    subtitle="Capacity snapshot and the maximum number of concurrent exam sessions."
  >
    <template #actions>
      <Badge :variant="capacity.variant">{{ capacity.label }}</Badge>
      <Button
        variant="secondary"
        size="sm"
        :loading="loading"
        :disabled="loading || saving"
        data-testid="resources-refresh"
        @click="emit('reload')"
      >
        <Icon name="refresh" :size="16" class="flex-none" />
        Refresh
      </Button>
    </template>

    <dl v-if="resources" class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
      <div>
        <dt class="text-text-muted">Running containers</dt>
        <dd class="m-0 font-medium text-text">{{ resources.running_containers }}</dd>
      </div>
      <div>
        <dt class="text-text-muted">Max sessions</dt>
        <dd class="m-0 font-medium text-text">{{ resources.max_concurrent_sessions }}</dd>
      </div>
      <div>
        <dt class="text-text-muted">Available memory</dt>
        <dd class="m-0 font-medium text-text">{{ formatMemMb(resources.available_mem_mb) }}</dd>
      </div>
      <div>
        <dt class="text-text-muted">Recommended max</dt>
        <dd class="m-0 font-medium text-text">{{ resources.recommended_max }}</dd>
      </div>
    </dl>

    <p v-if="resources && slots !== null" class="mt-3 text-xs text-text-muted">
      <template v-if="slots > 0">
        {{ slots }} slot{{ slots === 1 ? '' : 's' }} available.
      </template>
      <template v-else>
        Capacity reached ({{ resources.running_containers }}/{{
          resources.max_concurrent_sessions
        }}).
      </template>
    </p>

    <p v-if="resources && !resources.can_start" class="mt-1 text-xs text-warning-text">
      {{ resources.reason }}
    </p>

    <form
      class="mt-4 flex flex-col gap-3 border-t border-border pt-3"
      novalidate
      @submit.prevent="onSubmit"
    >
      <Input
        v-model="draft"
        type="number"
        label="Max concurrent sessions"
        hint="At least 1. Session creation is blocked once this many containers run."
        :error="error ?? undefined"
        :disabled="busy"
        data-testid="resources-max-input"
      />
      <div class="flex justify-end">
        <Button
          type="submit"
          variant="primary"
          :loading="saving"
          :disabled="!dirty || busy"
          data-testid="resources-save"
        >
          Save resource limit
        </Button>
      </div>
    </form>
  </Card>
</template>
