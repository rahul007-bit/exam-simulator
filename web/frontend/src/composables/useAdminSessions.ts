import { computed, ref } from 'vue'

import { listAdminSessions } from '@/api/admin'
import type { AdminSessionItem } from '@/api/admin'
import { apiRequest } from '@/api/client'

/**
 * useAdminSessions (FE-031, FE-036) — data + mutation layer for the admin
 * sessions table.
 *
 * Fetching reuses the typed client (`listAdminSessions`). The row actions are
 * thin wrappers around the existing admin endpoints:
 *
 *   POST /api/admin/sessions/{identifier}/terminate
 *   POST /api/admin/sessions/{identifier}/reset
 *   POST /api/admin/sessions/{identifier}/end
 *
 * `identifier` may be either a `session_id` (active/archived rows) or a
 * `candidate_token` (pending invites); the backend resolves either (parity with
 * the legacy admin prompts). The list is refreshed after every successful
 * mutation so the table reflects archived/removed rows.
 *
 * FE-036 makes mutations non-blocking (GCP-style): pending state is tracked
 * **per row identifier** (`pendingById`) instead of a single global flag, and
 * the table's `loading` is reserved for the initial load / explicit hard
 * reloads. Background refreshes flip `refreshing` and keep the current rows
 * mounted, so one in-flight action never blanks or locks the rest of the page.
 */

export type SessionAction = 'terminate' | 'reset' | 'end'

export interface AdminSessionMutationResult {
  status: string
  message: string
  scorecard?: unknown
}

/** Row actions permitted per row type, mirroring the legacy admin menu. */
export const ACTIONS_BY_TYPE: Record<AdminSessionItem['type'], readonly SessionAction[]> = {
  active: ['terminate', 'reset', 'end'],
  invite: ['terminate'],
  archived: ['terminate'],
}

/** Human label for an action, adjusted for the row type. */
export function sessionActionLabel(
  action: SessionAction,
  type: AdminSessionItem['type'],
): string {
  if (action === 'terminate') {
    if (type === 'invite') return 'Cancel invite'
    if (type === 'archived') return 'Delete record'
    return 'Terminate'
  }
  if (action === 'reset') return 'Reset exam'
  return 'End & grade'
}

/** Present-participle label used for the inline per-row pending indicator. */
export function sessionActionPendingLabel(action: SessionAction): string {
  if (action === 'terminate') return 'Terminating…'
  if (action === 'reset') return 'Resetting…'
  return 'Ending…'
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

export interface FetchSessionsOptions {
  /**
   * Force a background refresh. Background refreshes keep the existing rows in
   * place (`refreshing`) rather than blanking the table (`loading`).
   */
  silent?: boolean
}

export function useAdminSessions() {
  const sessions = ref<AdminSessionItem[]>([])
  /** Initial load / first paint only — drives `DataTable :loading`. */
  const loading = ref(false)
  /** Background refresh — rows stay mounted while this is true. */
  const refreshing = ref(false)
  const error = ref<string | null>(null)

  /** Pending action per row identifier (session id or candidate token). */
  const pendingById = ref<Map<string, SessionAction>>(new Map())
  /** True while any row has an action in flight (reference only). */
  const anyPending = computed(() => pendingById.value.size > 0)

  let loaded = false

  /** Resolve the endpoint identifier for a row (session id first, then token). */
  function identifierFor(session: AdminSessionItem): string | null {
    return session.session_id ?? session.candidate_token ?? null
  }

  function setPending(identifier: string, action: SessionAction): void {
    const next = new Map(pendingById.value)
    next.set(identifier, action)
    pendingById.value = next
  }

  function clearPending(identifier: string): void {
    if (!pendingById.value.has(identifier)) return
    const next = new Map(pendingById.value)
    next.delete(identifier)
    pendingById.value = next
  }

  /**
   * Load sessions. The first call (and any call before data has loaded once)
   * flips `loading`; later calls — including the post-mutation refresh — flip
   * `refreshing` unless `silent` is explicitly false.
   */
  async function fetchSessions(options: FetchSessionsOptions = {}): Promise<void> {
    const background = options.silent ?? loaded

    if (background) refreshing.value = true
    else loading.value = true
    error.value = null

    try {
      const response = await listAdminSessions()
      sessions.value = response.sessions
      loaded = true
    } catch (cause) {
      error.value = errorMessage(cause)
      throw cause
    } finally {
      loading.value = false
      refreshing.value = false
    }
  }

  async function runAction(
    identifier: string,
    action: SessionAction,
  ): Promise<AdminSessionMutationResult> {
    setPending(identifier, action)
    try {
      const result = await apiRequest<AdminSessionMutationResult>(
        `/api/admin/sessions/${encodeURIComponent(identifier)}/${action}`,
        { method: 'POST' },
      )
      await fetchSessions({ silent: true })
      return result
    } finally {
      clearPending(identifier)
    }
  }

  /** True if any action is in flight for the row. */
  function isRowPending(identifier: string): boolean {
    return pendingById.value.has(identifier)
  }

  /** The action currently in flight for the row, if any. */
  function pendingActionFor(identifier: string): SessionAction | undefined {
    return pendingById.value.get(identifier)
  }

  /** True only when the row's in-flight action matches `action`. */
  function isPending(identifier: string, action: SessionAction): boolean {
    return pendingById.value.get(identifier) === action
  }

  return {
    sessions,
    loading,
    refreshing,
    error,
    anyPending,
    pendingById,
    identifierFor,
    fetchSessions,
    runAction,
    isRowPending,
    pendingActionFor,
    isPending,
    ACTIONS_BY_TYPE,
    sessionActionLabel,
  }
}
