import { computed, ref } from 'vue'

import { apiRequest } from '@/api/client'

/**
 * useAdminInfrastructure (FE-034) — data + mutation layer for the admin fleet
 * infrastructure table.
 *
 * The typed client (`@/api/admin`) does not wrap the infrastructure routes, so
 * this composable calls them through `apiRequest` with local interfaces that
 * mirror the payload shapes emitted by `web/server.py`:
 *
 *   GET  /api/admin/infrastructure           -> { nodes, resources, summary }
 *   POST /api/admin/infrastructure/terminate -> { status, message }
 *        body: { kind: "docker" | "incus", node, name }
 *
 * `resources` merges Docker containers (`desktop_manager.list_all_docker_containers`)
 * and Incus instances (`incus_manager.list_all_fleet_instances`); both carry a
 * `kind` discriminator, while only Incus rows carry `ip`/`cpu_limit`/`mem_limit`.
 *
 * Reads throw to the caller (the view catches and toasts); mutations also
 * rethrow. The list is refreshed after every successful termination so a removed
 * row disappears. Pending work is tracked **per resource key** so the table
 * stays interactive and only the affected row shows an inline spinner.
 */

export type InfraResourceKind = 'docker' | 'incus'

export interface InfraNode {
  name: string
  ip: string
  role: string
  status: string
}

export interface InfraResource {
  name: string
  node: string
  kind: InfraResourceKind
  type: string
  status: string
  ip?: string
  image?: string
  session_id?: string
  cpu_limit?: string
  mem_limit?: string
  created_at?: string
}

export interface InfraSummary {
  total_nodes: number
  total_docker_containers: number
  total_incus_instances: number
  total_resources: number
}

export interface InfraSnapshot {
  nodes: InfraNode[]
  resources: InfraResource[]
  summary: InfraSummary
}

export interface TerminateResourceInput {
  kind: InfraResourceKind
  node: string
  name: string
}

export interface TerminateResourceResult {
  status: string
  message: string
}

export interface FetchInfrastructureOptions {
  /**
   * Force a background refresh. Background refreshes keep the existing rows in
   * place (`refreshing`) rather than blanking the table (`loading`).
   */
  silent?: boolean
}

/** Stable identity for a resource across refreshes (name may repeat per node). */
export function resourceKey(resource: Pick<InfraResource, 'kind' | 'node' | 'name'>): string {
  return `${resource.kind}:${resource.node}:${resource.name}`
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

export function useAdminInfrastructure() {
  const nodes = ref<InfraNode[]>([])
  const resources = ref<InfraResource[]>([])
  const summary = ref<InfraSummary | null>(null)

  /** Initial load / first paint only — drives `DataTable :loading`. */
  const loading = ref(false)
  /** Background refresh — rows stay mounted while this is true. */
  const refreshing = ref(false)
  const error = ref<string | null>(null)

  /** Pending termination per resource key. */
  const pendingByKey = ref<Set<string>>(new Set())
  /** True while any termination is in flight (reference only). */
  const anyPending = computed(() => pendingByKey.value.size > 0)

  let loaded = false

  /**
   * Load nodes + resources + summary. The first call (and any call before data
   * has loaded once) flips `loading`; later calls flip `refreshing` unless
   * `silent` is explicitly set otherwise.
   */
  async function fetchInfrastructure(options: FetchInfrastructureOptions = {}): Promise<void> {
    const background = options.silent ?? loaded

    if (background) refreshing.value = true
    else loading.value = true
    error.value = null

    try {
      const snapshot = await apiRequest<InfraSnapshot>('/api/admin/infrastructure')
      nodes.value = snapshot.nodes ?? []
      resources.value = snapshot.resources ?? []
      summary.value = snapshot.summary ?? null
      loaded = true
    } catch (cause) {
      error.value = errorMessage(cause)
      throw cause
    } finally {
      loading.value = false
      refreshing.value = false
    }
  }

  function setPending(key: string, pending: boolean): void {
    const next = new Set(pendingByKey.value)
    if (pending) next.add(key)
    else next.delete(key)
    pendingByKey.value = next
  }

  /**
   * Forcibly terminate a Docker container or Incus instance, then refresh the
   * inventory so the removed row disappears.
   */
  async function terminateResource(
    resource: TerminateResourceInput,
  ): Promise<TerminateResourceResult> {
    const key = resourceKey(resource)
    setPending(key, true)
    try {
      const result = await apiRequest<TerminateResourceResult>(
        '/api/admin/infrastructure/terminate',
        {
          method: 'POST',
          body: { kind: resource.kind, node: resource.node, name: resource.name },
        },
      )
      await fetchInfrastructure({ silent: true })
      return result
    } finally {
      setPending(key, false)
    }
  }

  /** True while a termination is in flight for the given resource. */
  function isRowPending(resource: Pick<InfraResource, 'kind' | 'node' | 'name'>): boolean {
    return pendingByKey.value.has(resourceKey(resource))
  }

  return {
    nodes,
    resources,
    summary,
    loading,
    refreshing,
    error,
    anyPending,
    pendingByKey,
    fetchInfrastructure,
    terminateResource,
    isRowPending,
  }
}
