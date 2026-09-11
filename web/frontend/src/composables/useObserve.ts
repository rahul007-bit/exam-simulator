import { computed, getCurrentInstance, onBeforeUnmount, ref, toValue, watch } from 'vue'
import type { ComputedRef, MaybeRefOrGetter, Ref } from 'vue'

import { ApiError, apiRequest } from '@/api/client'
import { buildNoVncUrl } from '@/composables/useVnc'

/**
 * useObserve (FE-035) — live admin observation of a single, explicitly named
 * session.
 *
 * The admin plane watches an active candidate session **view-only** by reusing
 * the imperative islands (`XTerm.vue` → `/ws/terminal/<sid>`, `NoVncFrame.vue`
 * → `/novnc/vnc.html?...&view_only=true&path=ws/desktop/<sid>`). This composable
 * owns everything around those transports:
 *
 *   - the explicit, never-fuzzy session target (no `active`/`default` fallback);
 *   - the detail feed: `GET /api/admin/session/{sid}` (singular route) with a
 *     poll refresh so the observed task list/progress tracks the candidate;
 *   - the admin mutations (plural routes):
 *       POST /api/admin/sessions/{sid}/terminate
 *       POST /api/admin/sessions/{sid}/reset
 *       POST /api/admin/sessions/{sid}/end
 *
 * **Cross-session safety.** Every URL/endpoint is derived from the single
 * `sessionId` getter passed in. A missing/blank id yields empty targets rather
 * than the legacy `active` sentinel — the server enforces this too (`/ws/terminal`
 * closes admins with code 1008 unless an explicit sid is given, `web/server.py:1694`).
 * A fetch that resolves after the target changed is discarded via a request
 * token, so a stale response can never populate the wrong session.
 *
 * Parity reference: the legacy admin observe mode.
 */

export type ObserveAction = 'terminate' | 'reset' | 'end'

/** Current-task payload from `GET /api/admin/session/{sid}`. */
export interface ObserveCurrentTask {
  task_num: number
  id: string
  title: string
  domain: string
  difficulty: string
  points: number
  target_context: string
  namespace: string
  description: string
  is_flagged: boolean
  score_data?: unknown
}

/** Per-question summary row from `GET /api/admin/session/{sid}`. */
export interface ObserveQuestionSummary {
  task_num: number
  id: string
  title: string
  points: number
  is_current: boolean
  is_flagged: boolean
  score_data?: unknown
}

/** Full detail response from `GET /api/admin/session/{sid}`. */
export interface ObserveSessionDetail {
  session_id: string
  candidate_token: string | null
  name: string | null
  status: string
  current_index: number
  total_tasks: number
  time_limit_minutes: number | null
  created_at: string | null
  current_task: ObserveCurrentTask | null
  container_running: boolean
  questions: ObserveQuestionSummary[]
}

/** Response from the admin session mutations. */
export interface ObserveActionResult {
  status: string
  message: string
  scorecard?: unknown
}

export interface UseObserveOptions {
  /** The explicit session id (or getter/ref) under observation. */
  sessionId: MaybeRefOrGetter<string | null | undefined>
  /**
   * Whether observation is currently on screen (the overlay's `open`). When
   * `false` the poll is stopped and no detail request is issued. Default `true`.
   */
  active?: MaybeRefOrGetter<boolean>
  /** Detail poll interval in ms. Clamped to >= 1000. Default 5000. */
  pollIntervalMs?: number
  /** Load + poll immediately when `active` and a session id are present. */
  autoStart?: boolean
}

export const DEFAULT_OBSERVE_POLL_MS = 5000

function normaliseSessionId(raw: unknown): string | null {
  const value = typeof raw === 'string' ? raw.trim() : ''
  return value.length > 0 ? value : null
}

function errorMessage(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

export function useObserve(options: UseObserveOptions) {
  const pollIntervalMs = Math.max(1000, options.pollIntervalMs ?? DEFAULT_OBSERVE_POLL_MS)

  const sessionId = computed<string | null>(() => normaliseSessionId(toValue(options.sessionId)))
  const active = computed<boolean>(() =>
    options.active === undefined ? true : Boolean(toValue(options.active)),
  )

  const detail = ref<ObserveSessionDetail | null>(null)
  /** Initial/explicit load (used for a full "loading" affordance). */
  const loading = ref(false)
  /** Background poll refresh while rows stay on screen. */
  const refreshing = ref(false)
  const error = ref<string | null>(null)
  /** Admin mutation currently in flight, if any. */
  const pendingAction = ref<ObserveAction | null>(null)

  /** True only when there is a concrete session to attach to. */
  const ready = computed<boolean>(() => sessionId.value !== null)

  /** Explicit terminal WS path for the observed session (empty when unset). */
  const terminalWsPath = computed<string>(() =>
    sessionId.value ? `/ws/terminal/${encodeURIComponent(sessionId.value)}` : '',
  )

  /** View-only noVNC URL for the desktop island (empty when unset). */
  const desktopUrl = computed<string>(() =>
    sessionId.value ? buildNoVncUrl(sessionId.value, { viewOnly: true }) : '',
  )

  let timer: ReturnType<typeof setInterval> | null = null
  let requestToken = 0

  /**
   * Fetch the session detail. Never throws during polling: a gone/archived
   * session (404) clears the soft error so the overlay can keep showing the
   * last known state; other failures are surfaced via `error`.
   */
  async function fetchDetail(fetchOptions: { silent?: boolean } = {}): Promise<
    ObserveSessionDetail | null
  > {
    const sid = sessionId.value
    if (!sid) {
      detail.value = null
      return null
    }

    const silent = fetchOptions.silent ?? detail.value !== null
    if (silent) refreshing.value = true
    else loading.value = true
    error.value = null

    const token = ++requestToken
    try {
      const data = await apiRequest<ObserveSessionDetail>(
        `/api/admin/session/${encodeURIComponent(sid)}`,
      )
      if (token !== requestToken || sessionId.value !== sid) return null
      detail.value = data
      return data
    } catch (cause) {
      if (token !== requestToken) return null
      if (cause instanceof ApiError && cause.status === 404) {
        error.value = null
      } else {
        error.value = errorMessage(cause)
      }
      return null
    } finally {
      if (token === requestToken) {
        loading.value = false
        refreshing.value = false
      }
    }
  }

  /** Run a single admin mutation against the explicit session id. */
  async function runAction(action: ObserveAction): Promise<ObserveActionResult> {
    const sid = sessionId.value
    if (!sid) throw new Error('No session selected for observation')

    pendingAction.value = action
    try {
      return await apiRequest<ObserveActionResult>(
        `/api/admin/sessions/${encodeURIComponent(sid)}/${action}`,
        { method: 'POST' },
      )
    } finally {
      pendingAction.value = null
    }
  }

  function startPolling(): void {
    if (timer !== null) return
    if (!ready.value || !active.value) return
    timer = setInterval(() => {
      void fetchDetail({ silent: true })
    }, pollIntervalMs)
  }

  function stopPolling(): void {
    if (timer === null) return
    clearInterval(timer)
    timer = null
  }

  /** Force an immediate refresh of the detail feed. */
  function refresh(): Promise<ObserveSessionDetail | null> {
    return fetchDetail({ silent: false })
  }

  function dispose(): void {
    stopPolling()
    requestToken += 1
    detail.value = null
    error.value = null
    pendingAction.value = null
  }

  watch(
    [sessionId, active],
    ([sid, isActive], [previousSid]) => {
      if (sid !== previousSid) {
        requestToken += 1
        detail.value = null
        error.value = null
        stopPolling()
      }
      if (!isActive || !sid) {
        stopPolling()
        return
      }
      if (sid !== previousSid || detail.value === null) void fetchDetail({ silent: false })
      startPolling()
    },
    { immediate: options.autoStart ?? true },
  )

  if (getCurrentInstance()) onBeforeUnmount(dispose)

  return {
    sessionId: sessionId as ComputedRef<string | null>,
    detail: detail as Ref<ObserveSessionDetail | null>,
    loading,
    refreshing,
    error,
    pendingAction,
    ready,
    terminalWsPath,
    desktopUrl,
    fetchDetail,
    refresh,
    runAction,
    startPolling,
    stopPolling,
    dispose,
  }
}
