<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import type { VNode } from 'vue'
import { useRouter } from 'vue-router'

import type { AdminSessionItem } from '@/api/admin'
import AdminConfigForm from '@/components/admin/AdminConfigForm.vue'
import AdminInfrastructureTable from '@/components/admin/AdminInfrastructureTable.vue'
import AdminInviteForm from '@/components/admin/AdminInviteForm.vue'
import AdminResourceForm from '@/components/admin/AdminResourceForm.vue'
import ObserveOverlay from '@/components/admin/ObserveOverlay.vue'
import SessionActionsDialog from '@/components/admin/SessionActionsDialog.vue'
import RecordingsModal from '@/components/candidate/RecordingsModal.vue'
import { Button, Card, DataTable, Icon, Spinner } from '@/components/ui'
import type { DataTableColumn } from '@/components/ui'
import type { ConfirmOptions } from '@/composables/useConfirm'
import { confirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import {
  sessionActionLabel,
  sessionActionPendingLabel,
  useAdminSessions,
} from '@/composables/useAdminSessions'
import type { SessionAction } from '@/composables/useAdminSessions'
import { useAdminConfig } from '@/composables/useAdminConfig'
import { buildInviteUrl, copyTextToClipboard, useAdminInvites } from '@/composables/useAdminInvites'
import { useAuthStore } from '@/stores/auth'

/**
 * Admin sessions surface (FE-031, FE-036).
 *
 * Lists active sessions, invitations and history from `/api/admin/sessions` in
 * the shared `DataTable` (sorting / filtering / pagination). Selecting a row
 * opens `SessionActionsDialog`; each action (terminate / reset / end) is gated
 * by the promise-based `useConfirm` dialog — never a native `confirm()` — and
 * reported through `useToast`.
 *
 * FE-036: mutations are non-blocking (GCP-style). Pending work is tracked per
 * row identifier, so the table stays populated and other rows remain fully
 * actionable while one row is terminating/resetting/ending. The affected row's
 * Actions cell shows an inline spinner + status, and the table's `loading` is
 * reserved for the initial load only.
 *
 * The route is already auth-gated by the FE-030 router guard, so this view
 * assumes an authenticated admin.
 *
 * FE-032: the page also hosts the global default-preset selector
 * (`AdminConfigForm` → `/api/admin/config`) and the server resource limit form
 * (`AdminResourceForm` → `/api/admin/resources`), each with inline validation
 * and toast feedback.
 *
 * TODO(assign-to-user): FS-004 will add an "assign to user" action. The
 * reserved slot lives in `components/admin/SessionActionsDialog.vue`.
 */

interface AdminSessionRow extends AdminSessionItem {
  actions: string
}

const auth = useAuthStore()
const router = useRouter()
const { push } = useToast()
const { sessions, loading, refreshing, fetchSessions, runAction, identifierFor, pendingActionFor } =
  useAdminSessions()
const {
  presetOptions,
  defaultPreset,
  resources,
  loading: configLoading,
  savingPreset,
  savingResources,
  presetName,
  loadAll: loadAdminConfig,
  saveDefaultPreset,
  saveMaxSessions,
} = useAdminConfig()
const { creating: inviteCreating, latestInvite, createInvite } = useAdminInvites()

const actionsOpen = ref(false)
const selected = ref<AdminSessionItem | null>(null)
const observeOpen = ref(false)
const observeTarget = ref<AdminSessionItem | null>(null)
const reviewOpen = ref(false)
const reviewTarget = ref<AdminSessionItem | null>(null)

function actionsCell(row: AdminSessionRow): VNode | string {
  const identifier = identifierFor(row)
  const action = identifier ? pendingActionFor(identifier) : undefined
  if (!action) return 'Manage…'
  return h(
    'span',
    {
      class: 'inline-flex items-center gap-1.5 text-text-muted',
      'data-testid': 'row-pending',
    },
    [h(Spinner, { size: 'sm', decorative: true }), sessionActionPendingLabel(action)],
  )
}

const columns: DataTableColumn<AdminSessionRow>[] = [
  {
    key: 'name',
    header: 'Session',
    accessor: (row) => `${row.name} ${row.session_id ?? ''}`,
    cell: (row) => row.name,
  },
  { key: 'type', header: 'Type', cell: (row) => row.type },
  { key: 'status', header: 'Status', cell: (row) => row.status },
  { key: 'candidate_token', header: 'Token', cell: (row) => row.candidate_token ?? '—' },
  {
    key: 'container_running',
    header: 'Container',
    align: 'center',
    cell: (row) => (row.container_running ? 'Running' : 'Stopped'),
  },
  {
    key: 'time_remaining_seconds',
    header: 'Time left',
    align: 'right',
    cell: (row) => timeRemainingLabel(row),
  },
  { key: 'created_at', header: 'Created', cell: (row) => formatTimestamp(row.created_at) },
  {
    key: 'actions',
    header: 'Actions',
    sortable: false,
    filterable: false,
    align: 'right',
    // Rendered through TanStack `FlexRender`, which accepts a VNode result.
    cell: (row) => actionsCell(row) as unknown as string,
  },
]

const rows = computed<AdminSessionRow[]>(() =>
  sessions.value.map((session) => ({ ...session, actions: 'Manage…' })),
)

const selectedPendingAction = computed<SessionAction | null>(() => {
  const session = selected.value
  if (!session) return null
  const identifier = identifierFor(session)
  return (identifier ? pendingActionFor(identifier) : undefined) ?? null
})

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

function timeRemainingLabel(row: AdminSessionItem): string {
  if (row.status === 'pending') return 'Waiting'
  if (row.status === 'active') {
    const seconds = row.time_remaining_seconds
    if (seconds == null) return 'Untimed'
    if (seconds <= 0) return 'Ended'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    return `${pad(hours)}:${pad(minutes)}:${pad(seconds % 60)}`
  }
  return 'Ended'
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function rowKey(row: AdminSessionRow): string {
  return row.session_id ?? row.candidate_token ?? row.name
}

function confirmOptions(action: SessionAction, session: AdminSessionItem): ConfirmOptions {
  const label = sessionActionLabel(action, session.type)
  const identifier = identifierFor(session) ?? session.name
  const messages: Record<SessionAction, string> = {
    terminate: `This permanently removes "${session.name}" (${identifier}) and frees all of its resources.`,
    reset: `This clears the active exam for "${session.name}" and resets the cluster namespaces.`,
    end: `This ends and evaluates "${session.name}" now, then archives the session.`,
  }
  return { title: `${label}?`, message: messages[action], confirmLabel: label, danger: true }
}

function describeError(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

async function refresh(): Promise<void> {
  try {
    await fetchSessions()
  } catch (cause) {
    push({ variant: 'error', message: describeError(cause) })
  }
}

async function refreshAdminConfig(): Promise<void> {
  try {
    await loadAdminConfig()
  } catch (cause) {
    push({ variant: 'error', message: describeError(cause) })
  }
}

async function onSavePreset(preset: string): Promise<void> {
  try {
    await saveDefaultPreset(preset)
    push({ variant: 'success', message: `Default preset set to ${presetName(preset) ?? preset}` })
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not save default preset',
      message: describeError(cause),
    })
  }
}

async function onSaveMaxSessions(limit: number): Promise<void> {
  try {
    await saveMaxSessions(limit)
    push({ variant: 'success', message: `Concurrency limit updated to ${limit}` })
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not update resource limit',
      message: describeError(cause),
    })
  }
}

function onInvalidMaxSessions(message: string): void {
  push({ variant: 'warning', message })
}

async function onCreateInvite(preset: string): Promise<void> {
  try {
    const invite = await createInvite(preset || undefined)
    await copyTextToClipboard(buildInviteUrl(invite.url))
    push({ variant: 'success', message: 'Candidate link generated & copied!' })
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not create invite',
      message: describeError(cause),
    })
  }
}

async function onCopyInvite(url: string): Promise<void> {
  try {
    await copyTextToClipboard(url)
    push({ variant: 'success', message: 'Invite link copied to clipboard!' })
  } catch (cause) {
    push({ variant: 'error', message: describeError(cause) })
  }
}

function onRowClick(row: AdminSessionRow): void {
  if (!identifierFor(row)) {
    push({ variant: 'warning', message: 'This row has no session id or token to act on.' })
    return
  }
  selected.value = row
  actionsOpen.value = true
}

async function onAction(action: SessionAction): Promise<void> {
  const session = selected.value
  if (!session) return
  const identifier = identifierFor(session)
  if (!identifier) return

  actionsOpen.value = false
  const approved = await confirm(confirmOptions(action, session))
  if (!approved) {
    selected.value = null
    return
  }

  try {
    const result = await runAction(identifier, action)
    push({
      variant: 'success',
      message: result.message || `${sessionActionLabel(action, session.type)} completed`,
    })
  } catch (cause) {
    push({ variant: 'error', message: describeError(cause) })
  } finally {
    selected.value = null
  }
}

async function onLogout(): Promise<void> {
  await auth.logout()
  push({ variant: 'success', message: 'Signed out of the admin plane' })
  await router.replace({ name: 'login' })
}

/** Open the FE-035 observe overlay for the selected active session. */
function onObserve(): void {
  const session = selected.value
  if (!session?.session_id) return
  observeTarget.value = session
  observeOpen.value = true
  actionsOpen.value = false
}

/** After an observe overlay action, close it and refresh the list in the background. */
function onObserveAction(): void {
  observeOpen.value = false
  void fetchSessions({ silent: true })
}

/** Open the FE-029 recordings/replay surface scoped to the selected session. */
function onReview(): void {
  const session = selected.value
  if (!session?.session_id) {
    push({ variant: 'warning', message: 'This session has no recording id yet.' })
    return
  }
  reviewTarget.value = session
  reviewOpen.value = true
  actionsOpen.value = false
}

onMounted(() => {
  void refresh()
  void refreshAdminConfig()
})
</script>

<template>
  <main class="mx-auto w-full max-w-6xl p-4">
    <div class="flex flex-col gap-4">
      <Card
        title="Admin plane"
        subtitle="Signed in as an administrator. Manage exam sessions, invitations and history."
      >
        <template #actions>
          <Button variant="secondary" :loading="auth.loading" @click="onLogout"> Sign out </Button>
        </template>
        <p class="m-0 text-sm text-text-muted">
          Manage the default preset, server capacity and exam sessions from this page.
        </p>
      </Card>

      <div class="grid gap-4 lg:grid-cols-2">
        <div class="flex flex-col gap-4">
          <AdminConfigForm
            :saved="defaultPreset"
            :options="presetOptions"
            :loading="configLoading"
            :saving="savingPreset"
            @save="onSavePreset"
            @reload="refreshAdminConfig"
          />

          <AdminInviteForm
            :options="presetOptions"
            :invite="latestInvite"
            :creating="inviteCreating"
            @create="onCreateInvite"
            @copy="onCopyInvite"
          />
        </div>

        <AdminResourceForm
          :resources="resources"
          :loading="configLoading"
          :saving="savingResources"
          @save="onSaveMaxSessions"
          @invalid="onInvalidMaxSessions"
          @reload="refreshAdminConfig"
        />
      </div>

      <Card title="Sessions" subtitle="Active exams, invitations and history">
        <template #actions>
          <Button
            variant="secondary"
            size="sm"
            :loading="refreshing || loading"
            :disabled="refreshing || loading"
            data-testid="sessions-refresh"
            @click="refresh"
          >
            <Icon name="refresh" :size="16" class="flex-none" />
            Refresh
          </Button>
        </template>

        <DataTable
          :data="rows"
          :columns="columns"
          caption="Admin sessions, invitations and history"
          search-label="Filter sessions"
          search-placeholder="Filter by name, session ID, type, status or token"
          :loading="loading"
          :page-size="10"
          :row-key="rowKey"
          interactive
          empty-message="No sessions, invitations or history yet."
          loading-label="Loading sessions"
          @row-click="onRowClick"
        />

        <p class="mt-3 text-xs text-text-muted">
          Select a row to terminate, reset or end that session. Every action is confirmed before it
          runs.
        </p>
      </Card>

      <AdminInfrastructureTable />
    </div>

    <SessionActionsDialog
      v-model="actionsOpen"
      :session="selected"
      :pending-action="selectedPendingAction"
      @action="onAction"
      @observe="onObserve"
      @review="onReview"
    />

    <RecordingsModal
      v-model="reviewOpen"
      :initial-session-id="reviewTarget?.session_id ?? ''"
      :show-list="false"
    />

    <ObserveOverlay
      :open="observeOpen"
      :session-id="observeTarget?.session_id ?? ''"
      :session-name="observeTarget?.name"
      @close="observeOpen = false"
      @action="onObserveAction"
    />
  </main>
</template>
