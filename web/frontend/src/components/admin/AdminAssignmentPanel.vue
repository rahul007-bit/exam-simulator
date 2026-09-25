<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import type { VNode } from 'vue'

import {
  createAssignment,
  deleteAssignment,
  listAdminAssignments,
} from '@/api/assignments'
import type { Assignment } from '@/api/assignments'
import { Badge, Button, Card, DataTable, Icon, Input, Select, Spinner } from '@/components/ui'
import type { BadgeVariant, DataTableColumn, SelectOption } from '@/components/ui'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { usePresetsStore } from '@/stores/presets'

/**
 * AdminAssignmentPanel (FS-004) — assign an exam preset to a named user.
 *
 * Assignments reuse the invitation/token flow (D-011): the form creates a
 * user-bound invitation via `POST /api/admin/assignments`, and the table lists
 * the existing assignments from `GET /api/admin/assignments`. Deletions are
 * gated by the promise-based `useConfirm` dialog and reported through
 * `useToast`. Preset options come from the shared presets store.
 *
 * Colours resolve to design tokens only (no raw hex or emoji).
 */

const props = withDefaults(defineProps<{ active?: boolean }>(), { active: true })

const { push } = useToast()
const { confirm } = useConfirm()
const presets = usePresetsStore()

const assignments = ref<Assignment[]>([])
const loading = ref(false)
const refreshing = ref(false)
const assigning = ref(false)
const deletingId = ref<string | null>(null)
const username = ref('')
const preset = ref('')

let loaded = false

const presetOptions = computed<SelectOption[]>(() =>
  presets.presets.map((item) => ({ value: item.filename, label: item.name })),
)
const canAssign = computed(
  () => username.value.trim() !== '' && preset.value !== '' && !assigning.value,
)

function describeError(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

function statusVariant(status: string | undefined): BadgeVariant {
  const value = (status ?? '').toLowerCase()
  if (value === 'pending') return 'warning'
  if (value === 'started' || value === 'active') return 'success'
  if (value === 'expired') return 'neutral'
  return 'info'
}

function formatDate(value: string): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

async function ensurePresets(): Promise<void> {
  if (presets.presets.length === 0) await presets.fetchPresets()
}

async function refresh(): Promise<void> {
  const background = loaded
  if (background) refreshing.value = true
  else loading.value = true
  try {
    const response = await listAdminAssignments()
    assignments.value = response.assignments
    loaded = true
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not load assignments',
      message: describeError(cause),
    })
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function load(): Promise<void> {
  await Promise.all([refresh(), ensurePresets().catch(() => undefined)])
}

onMounted(() => {
  if (props.active) void load()
})

watch(
  () => props.active,
  (active) => {
    if (active) void load()
  },
)

async function onAssign(): Promise<void> {
  if (!canAssign.value) return
  const targetUser = username.value.trim()
  assigning.value = true
  try {
    const result = await createAssignment(targetUser, preset.value)
    push({
      variant: 'success',
      message: `Assigned "${result.assignment.preset}" to ${targetUser}.`,
    })
    username.value = ''
    preset.value = ''
    await refresh()
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not assign exam',
      message: describeError(cause),
    })
  } finally {
    assigning.value = false
  }
}

async function onDelete(row: Assignment): Promise<void> {
  const approved = await confirm({
    title: 'Delete assignment?',
    message: `This removes the "${row.preset}" assignment for "${row.username}". This cannot be undone.`,
    confirmLabel: 'Delete',
    danger: true,
  })
  if (!approved) return

  deletingId.value = row.id
  try {
    await deleteAssignment(row.id)
    push({ variant: 'success', message: `Deleted assignment for ${row.username}.` })
    await refresh()
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not delete assignment',
      message: describeError(cause),
    })
  } finally {
    deletingId.value = null
  }
}

function statusCell(row: Assignment): VNode | string {
  return h(Badge, { variant: statusVariant(row.status) }, () => row.status || 'pending')
}

function actionsCell(row: Assignment): VNode | string {
  if (deletingId.value === row.id) {
    return h(
      'span',
      {
        class: 'inline-flex items-center gap-1.5 text-text-muted',
        'data-testid': 'assignment-pending',
      },
      [h(Spinner, { size: 'sm', decorative: true }), 'Deleting…'],
    )
  }
  return h(
    Button,
    {
      variant: 'danger',
      size: 'sm',
      'data-testid': `assignment-delete-${row.id}`,
      onClick: () => void onDelete(row),
    },
    () => [h(Icon, { name: 'error', size: 14, class: 'flex-none' }), 'Delete'],
  )
}

const columns: DataTableColumn<Assignment>[] = [
  { key: 'username', header: 'User' },
  { key: 'preset', header: 'Preset' },
  { key: 'assigned_by', header: 'Assigned by', cell: (row) => row.assigned_by || '—' },
  {
    key: 'status',
    header: 'Status',
    align: 'center',
    cell: (row) => statusCell(row) as unknown as string,
  },
  { key: 'created_at', header: 'Created', cell: (row) => formatDate(row.created_at) },
  {
    key: 'url',
    header: 'Link',
    sortable: false,
    cell: (row) => (row.url ? 'Invite link' : '—'),
  },
  {
    key: 'id',
    header: 'Actions',
    sortable: false,
    filterable: false,
    align: 'right',
    cell: (row) => actionsCell(row) as unknown as string,
  },
]

function rowKey(row: Assignment): string {
  return row.id
}

defineExpose({ refresh, loading, refreshing })
</script>

<template>
  <Card
    title="Assign exam"
    subtitle="Assign an exam preset directly to a named user. They start it from their own assignment list."
  >
    <template #actions>
      <Button
        variant="secondary"
        size="sm"
        :loading="refreshing || loading"
        :disabled="refreshing || loading"
        data-testid="assignment-refresh"
        @click="refresh"
      >
        <Icon name="refresh" :size="16" class="flex-none" />
        Refresh
      </Button>
    </template>

    <form
      class="flex flex-col gap-3 sm:flex-row sm:items-end"
      novalidate
      @submit.prevent="onAssign"
    >
      <div class="flex-1">
        <Input
          v-model="username"
          label="Username"
          placeholder="candidate username"
          autocomplete="off"
          :disabled="assigning"
          data-testid="assignment-username"
        />
      </div>

      <div class="flex-1">
        <Select
          :model-value="preset"
          :options="presetOptions"
          label="Exam preset"
          placeholder="Select a preset"
          :disabled="assigning"
          data-testid="assignment-preset"
          @update:model-value="preset = $event"
        />
      </div>

      <Button
        type="submit"
        variant="primary"
        :loading="assigning"
        :disabled="!canAssign"
        data-testid="assignment-create"
      >
        Assign
      </Button>
    </form>

    <div class="mt-4 flex flex-col gap-3">
      <DataTable
        :data="assignments"
        :columns="columns"
        caption="User exam assignments"
        search-label="Filter assignments"
        search-placeholder="Filter by user, preset, status or assigner"
        :loading="loading"
        :page-size="10"
        :row-key="rowKey"
        empty-message="No assignments yet. Assign an exam to a user above."
        loading-label="Loading assignments"
      />

      <p class="m-0 text-xs text-text-muted">
        Assignments are user-bound invitation links. Deleting one revokes the link before it is
        used.
      </p>
    </div>
  </Card>
</template>
