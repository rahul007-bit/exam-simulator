<script setup lang="ts">
import { computed, h, onMounted, watch } from 'vue'
import type { VNode } from 'vue'

import { Badge, Button, Card, DataTable, Icon, Spinner } from '@/components/ui'
import type { BadgeVariant, DataTableColumn } from '@/components/ui'
import { useConfirm } from '@/composables/useConfirm'
import { useToast } from '@/composables/useToast'
import { useAdminInfrastructure } from '@/composables/useAdminInfrastructure'
import type { InfraResource } from '@/composables/useAdminInfrastructure'

/**
 * AdminInfrastructureTable (FE-034) — self-contained fleet inventory surface.
 *
 * Renders the counts from `/api/admin/infrastructure`, a card per fleet node,
 * and a `DataTable` merging Docker containers and Incus instances. Each resource
 * row offers a **Terminate** action that is gated by the promise-based
 * `useConfirm` dialog (never a native `confirm()`) and reported through
 * `useToast`; the row shows an inline spinner while the request is in flight.
 *
 * The component fetches on mount when `active` (default `true`) and re-fetches
 * whenever `active` flips back to true. Parents can drive it imperatively via
 * the exposed `refresh()` method (e.g. from a page-level Refresh button).
 *
 * Colours resolve to design tokens only (no raw hex, glow or emoji).
 */

const props = withDefaults(
  defineProps<{
    /**
     * When true the table loads on mount and refreshes on each activation
     * (e.g. when the hosting tab becomes visible). When false it stays idle
     * until `refresh()` is called.
     */
    active?: boolean
  }>(),
  { active: true },
)

interface InfraResourceRow extends InfraResource {
  pending: boolean
  actions: string
}

const { push } = useToast()
const { confirm } = useConfirm()
const {
  nodes,
  resources,
  summary,
  loading,
  refreshing,
  error,
  fetchInfrastructure,
  terminateResource,
  isRowPending,
} = useAdminInfrastructure()

function describeError(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

async function refresh(): Promise<void> {
  try {
    await fetchInfrastructure()
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not load infrastructure',
      message: describeError(cause),
    })
  }
}

onMounted(() => {
  if (props.active) void refresh()
})

watch(
  () => props.active,
  (active) => {
    if (active) void refresh()
  },
)

const rows = computed<InfraResourceRow[]>(() =>
  resources.value.map((resource) => ({
    ...resource,
    pending: isRowPending(resource),
    actions: 'Terminate',
  })),
)

function kindLabel(row: InfraResource): string {
  return row.kind === 'docker' ? 'Docker' : 'Incus'
}

function kindVariant(kind: InfraResource['kind']): BadgeVariant {
  return kind === 'docker' ? 'info' : 'accent'
}

function statusVariant(status: string | undefined): BadgeVariant {
  const value = (status ?? '').toLowerCase()
  if (value.includes('running') || value.includes(' up')) return 'success'
  if (
    value.includes('exit') ||
    value.includes('stop') ||
    value.includes('error') ||
    value.includes('fail')
  ) {
    return 'danger'
  }
  return 'neutral'
}

function sessionLabel(row: InfraResource): string {
  const session = row.session_id
  if (!session || session === '-') return '—'
  return session.length > 14 ? `${session.slice(0, 14)}…` : session
}

function limitsLabel(row: InfraResource): string {
  if (row.kind !== 'incus') return 'Host default'
  const cpu = row.cpu_limit && row.cpu_limit !== '-' ? row.cpu_limit : null
  const mem = row.mem_limit && row.mem_limit !== '-' ? row.mem_limit : null
  if (!cpu && !mem) return 'Host default'
  return [cpu ? `${cpu} vCPU` : null, mem].filter((part): part is string => part !== null).join(', ')
}

function kindCell(row: InfraResourceRow): VNode | string {
  return h(Badge, { variant: kindVariant(row.kind) }, () => kindLabel(row))
}

function statusCell(row: InfraResourceRow): VNode | string {
  const status = row.status || 'Unknown'
  return h(Badge, { variant: statusVariant(row.status) }, () => status)
}

function actionsCell(row: InfraResourceRow): VNode | string {
  if (row.pending) {
    return h(
      'span',
      {
        class: 'inline-flex items-center gap-1.5 text-text-muted',
        'data-testid': 'infra-pending',
      },
      [h(Spinner, { size: 'sm', decorative: true }), 'Terminating…'],
    )
  }
  return h(
    Button,
    {
      variant: 'danger',
      size: 'sm',
      'data-testid': `infra-terminate-${row.kind}`,
      onClick: () => void onTerminate(row),
    },
    () => [h(Icon, { name: 'error', size: 14, class: 'flex-none' }), 'Terminate'],
  )
}

const columns: DataTableColumn<InfraResourceRow>[] = [
  { key: 'name', header: 'Resource' },
  { key: 'node', header: 'Node' },
  { key: 'kind', header: 'Kind', align: 'center', cell: (row) => kindCell(row) as unknown as string },
  { key: 'session_id', header: 'Session', cell: (row) => sessionLabel(row) },
  { key: 'ip', header: 'IP', cell: (row) => row.ip ?? '—' },
  { key: 'cpu_limit', header: 'Limits', cell: (row) => limitsLabel(row) },
  {
    key: 'status',
    header: 'Status',
    align: 'center',
    cell: (row) => statusCell(row) as unknown as string,
  },
  {
    key: 'actions',
    header: 'Actions',
    sortable: false,
    filterable: false,
    align: 'right',
    cell: (row) => actionsCell(row) as unknown as string,
  },
]

function rowKey(row: InfraResourceRow): string {
  return `${row.kind}:${row.node}:${row.name}`
}

async function onTerminate(row: InfraResourceRow): Promise<void> {
  const approved = await confirm({
    title: `Terminate ${row.kind} resource?`,
    message: `This forcibly removes "${row.name}" on node "${row.node}". This cannot be undone.`,
    confirmLabel: 'Terminate',
    danger: true,
  })
  if (!approved) return

  try {
    const result = await terminateResource(row)
    push({
      variant: 'success',
      message: result.message || `Terminated ${row.name}`,
    })
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not terminate resource',
      message: describeError(cause),
    })
  }
}

defineExpose({ refresh, loading, refreshing })
</script>

<template>
  <Card
    title="Fleet infrastructure"
    subtitle="Nodes and the Docker containers / Incus instances running across the fleet."
  >
    <template #actions>
      <Button
        variant="secondary"
        size="sm"
        :loading="refreshing || loading"
        :disabled="refreshing || loading"
        data-testid="infra-refresh"
        @click="refresh"
      >
        <Icon name="refresh" :size="16" class="flex-none" />
        Refresh
      </Button>
    </template>

    <div class="flex flex-col gap-4">
      <dl v-if="summary" class="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="rounded-[var(--radius-md)] border border-border bg-elevated p-3">
          <dt class="text-xs text-text-muted">Nodes</dt>
          <dd class="m-0 text-lg font-semibold text-text">{{ summary.total_nodes }}</dd>
        </div>
        <div class="rounded-[var(--radius-md)] border border-border bg-elevated p-3">
          <dt class="text-xs text-text-muted">Docker containers</dt>
          <dd class="m-0 text-lg font-semibold text-text">{{ summary.total_docker_containers }}</dd>
        </div>
        <div class="rounded-[var(--radius-md)] border border-border bg-elevated p-3">
          <dt class="text-xs text-text-muted">Incus instances</dt>
          <dd class="m-0 text-lg font-semibold text-text">{{ summary.total_incus_instances }}</dd>
        </div>
        <div class="rounded-[var(--radius-md)] border border-border bg-elevated p-3">
          <dt class="text-xs text-text-muted">Total resources</dt>
          <dd class="m-0 text-lg font-semibold text-text">{{ summary.total_resources }}</dd>
        </div>
      </dl>

      <div v-if="nodes.length" class="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <div
          v-for="node in nodes"
          :key="node.name"
          class="rounded-[var(--radius-md)] border border-border bg-surface p-3"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="truncate font-semibold text-text">{{ node.name }}</span>
            <Badge :variant="statusVariant(node.status)">{{ node.status }}</Badge>
          </div>
          <p class="m-0 mt-1 font-mono text-xs text-text-muted">{{ node.ip }}</p>
          <p class="m-0 mt-0.5 text-xs text-text-muted">{{ node.role }}</p>
        </div>
      </div>

      <p v-if="error && !loading" class="m-0 text-sm text-danger-text" data-testid="infra-error">
        {{ error }}
      </p>

      <DataTable
        :data="rows"
        :columns="columns"
        caption="Fleet nodes and resources"
        search-label="Filter resources"
        search-placeholder="Filter by name, node, kind, session or status"
        :loading="loading"
        :page-size="10"
        :row-key="rowKey"
        empty-message="No active containers or Incus instances running in the fleet."
        loading-label="Loading infrastructure"
      />

      <p class="m-0 text-xs text-text-muted">
        Terminating a resource forcibly removes the container or instance from its node. Every
        termination is confirmed before it runs.
      </p>
    </div>
  </Card>
</template>
