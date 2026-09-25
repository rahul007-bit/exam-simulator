<script setup lang="ts">
import { computed } from 'vue'

import type { AdminSessionItem } from '@/api/admin'
import type { SessionAction } from '@/composables/useAdminSessions'
import { ACTIONS_BY_TYPE, sessionActionLabel } from '@/composables/useAdminSessions'
import { Badge, Button, Icon, Modal } from '@/components/ui'
import type { BadgeVariant, IconName } from '@/components/ui'

/**
 * SessionActionsDialog (FE-031) — the row-action surface for the admin sessions
 * table. `DataTable` rows are `interactive`, so selecting a row opens this modal
 * with the actions the row's type permits (parity with the legacy admin menu):
 *
 *   active   -> terminate / reset / end
 *   invite   -> terminate (cancel invite)
 *   archived -> terminate (delete record)
 *
 * The dialog is presentational: it never calls the API itself. It emits the
 * chosen action and the parent runs it through `useConfirm` (no native
 * `confirm()`), then `useToast`.
 */

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    session: AdminSessionItem | null
    /** Action currently in flight for this session, if any (FE-036). */
    pendingAction?: SessionAction | null
  }>(),
  { pendingAction: null },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  action: [action: SessionAction]
  observe: []
  review: []
}>()

const TYPE_VARIANT: Record<AdminSessionItem['type'], BadgeVariant> = {
  active: 'success',
  invite: 'warning',
  archived: 'neutral',
}

const ACTION_ICON: Record<SessionAction, IconName> = {
  terminate: 'error',
  reset: 'refresh',
  end: 'check',
}

const type = computed<AdminSessionItem['type']>(() => props.session?.type ?? 'archived')

const actions = computed<readonly SessionAction[]>(() => ACTIONS_BY_TYPE[type.value])

/** A pending action disables only this row's action buttons; Close stays live. */
const sessionPending = computed(() => props.pendingAction != null)

/** Only live sessions with a concrete id can be observed (FE-035). */
const canObserve = computed(() => type.value === 'active' && Boolean(props.session?.session_id))

const identifier = computed(
  () => props.session?.session_id ?? props.session?.candidate_token ?? null,
)

function statusVariant(status: string | undefined): BadgeVariant {
  switch (status) {
    case 'active':
      return 'success'
    case 'pending':
      return 'warning'
    case 'submitted':
    case 'completed':
      return 'info'
    case 'expired':
    case 'terminated':
    case 'reset':
    case 'replaced':
      return 'danger'
    default:
      return 'neutral'
  }
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function label(action: SessionAction): string {
  return sessionActionLabel(action, type.value)
}

function close(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <Modal
    :model-value="modelValue"
    title="Manage session"
    :description="session ? session.name : 'Session actions'"
    size="md"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="session" class="flex flex-col gap-3">
      <dl class="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
        <dt class="text-text-muted">Name</dt>
        <dd class="m-0 truncate font-medium text-text">{{ session.name }}</dd>

        <dt class="text-text-muted">Type</dt>
        <dd class="m-0">
          <Badge :variant="TYPE_VARIANT[session.type]">{{ session.type }}</Badge>
        </dd>

        <dt class="text-text-muted">Status</dt>
        <dd class="m-0">
          <Badge :variant="statusVariant(session.status)">{{ session.status }}</Badge>
        </dd>

        <dt class="text-text-muted">Identifier</dt>
        <dd class="m-0 truncate font-mono text-xs text-text">
          {{ identifier ?? 'Not available' }}
        </dd>

        <dt class="text-text-muted">Created</dt>
        <dd class="m-0 text-text">{{ formatTimestamp(session.created_at) }}</dd>
      </dl>

      <div class="grid grid-cols-2 gap-2 border-t border-border pt-3">
        <Button
          v-if="canObserve"
          variant="secondary"
          block
          :disabled="sessionPending"
          data-testid="session-action-observe"
          @click="emit('observe')"
        >
          <Icon name="desktop" :size="16" class="flex-none" />
          Observe live
        </Button>

        <Button
          v-if="identifier"
          variant="secondary"
          block
          :disabled="sessionPending"
          data-testid="session-action-review"
          @click="emit('review')"
        >
          <Icon name="play" :size="16" class="flex-none" />
          Review &amp; replay
        </Button>

        <Button
          v-for="action in actions"
          :key="action"
          :variant="action === 'terminate' ? 'danger' : action === 'reset' ? 'secondary' : 'primary'"
          block
          :disabled="sessionPending"
          :loading="pendingAction === action"
          :data-testid="`session-action-${action}`"
          @click="emit('action', action)"
        >
          <Icon :name="ACTION_ICON[action]" :size="16" class="flex-none" />
          {{ label(action) }}
        </Button>

        <!-- TODO(assign-to-user): FS-004 will add the "Assign to user" action here,
             positioned above the destructive actions once ownership lands. -->
      </div>
    </div>

    <template #footer>
      <Button variant="ghost" data-testid="session-actions-close" @click="close">Close</Button>
    </template>
  </Modal>
</template>
