<script setup lang="ts">
import { computed, ref } from 'vue'

import type { CreateSessionInviteResponse } from '@/api/admin'
import { Badge, Button, Card, Icon, Select } from '@/components/ui'
import type { SelectOption } from '@/components/ui'
import { buildInviteUrl } from '@/composables/useAdminInvites'

/**
 * AdminInviteForm (FE-033) — the "create candidate invite" card.
 *
 * Presentational: the preset catalogue arrives via `options`, the generated
 * invite via `invite`, and the two actions are emitted (`create` on Generate
 * link, `copy` with the absolute URL on Copy link). The view owns the API call,
 * the clipboard write and the toasts, mirroring `AdminConfigForm`.
 */

const props = withDefaults(
  defineProps<{
    options: SelectOption[]
    invite?: CreateSessionInviteResponse | null
    creating?: boolean
    starting?: boolean
    disabled?: boolean
  }>(),
  { invite: null, creating: false, starting: false, disabled: false },
)

const emit = defineEmits<{
  create: [preset: string]
  copy: [url: string]
  start: [token: string]
}>()

const preset = ref('')

const busy = computed(() => props.creating || props.disabled)
const displayUrl = computed(() => (props.invite ? buildInviteUrl(props.invite.url) : ''))

function onGenerate(): void {
  if (busy.value) return
  emit('create', preset.value)
}

function onCopy(): void {
  if (!displayUrl.value) return
  emit('copy', displayUrl.value)
}

function onStart(): void {
  if (busy.value || props.starting || !props.invite?.token) return
  emit('start', props.invite.token)
}
</script>

<template>
  <Card
    title="Create candidate invite"
    subtitle="Generate a unique exam link pre-assigned to a candidate."
  >
    <form class="flex flex-col gap-3" novalidate @submit.prevent="onGenerate">
      <Select
        :model-value="preset"
        :options="options"
        label="Assign exam preset"
        placeholder="Default preset"
        :disabled="busy"
        data-testid="invite-preset"
        @update:model-value="preset = $event"
      />

      <div class="flex justify-end">
        <Button
          type="submit"
          variant="primary"
          :loading="creating"
          :disabled="busy"
          data-testid="invite-generate"
        >
          Generate link
        </Button>
      </div>
    </form>

    <div
      v-if="invite"
      class="mt-4 flex flex-col gap-2 rounded-[var(--radius-sm)] border border-border bg-surface p-3"
      data-testid="invite-output"
    >
      <div class="flex items-center justify-between gap-2">
        <span class="text-xs font-semibold text-text-muted">New candidate invite link</span>
        <Badge variant="accent">{{ invite.preset }}</Badge>
      </div>

      <span class="break-all font-mono text-xs text-accent-text" data-testid="invite-url">
        {{ displayUrl }}
      </span>

      <div class="flex justify-end gap-2">
        <Button variant="secondary" size="sm" data-testid="invite-copy" @click="onCopy">
          <Icon name="copy" :size="14" class="flex-none" />
          Copy link
        </Button>
        <Button
          variant="primary"
          size="sm"
          :loading="starting"
          :disabled="busy || starting"
          data-testid="invite-start"
          @click="onStart"
        >
          Start now
        </Button>
      </div>
    </div>
  </Card>
</template>
