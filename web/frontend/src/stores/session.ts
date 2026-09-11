import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as sessionApi from '@/api/session'
import * as actionsApi from '@/api/actions'
import type { SubmitResponse } from '@/api/actions'
import type {
  PresetLockedInfo,
  SessionQuery,
  SessionResponse,
  StartRequest,
  TaskData,
} from '@/api/session'

export const useSessionStore = defineStore('session', () => {
  const data = ref<SessionResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isActive = computed(() => data.value?.active === true)
  const isInvited = computed(() => {
    const current = data.value
    return current !== null && current.active === false && 'invited' in current
      ? current.invited === true
      : false
  })
  const isAdmin = computed(() => {
    const current = data.value
    return current !== null && 'is_admin' in current ? current.is_admin : false
  })
  const isLocked = computed(() => {
    const current = data.value
    return (
      current !== null && current.active === false && 'locked' in current && current.locked === true
    )
  })
  const sessionId = computed(() => (data.value?.active === true ? data.value.session_id : null))
  const currentTask = computed<TaskData | null>(() =>
    data.value?.active === true ? (data.value.current_task ?? null) : null,
  )
  const totalTasks = computed(() => (data.value?.active === true ? data.value.total_tasks : 0))
  const currentTaskNum = computed(() =>
    data.value?.active === true ? data.value.current_index + 1 : 0,
  )
  const flaggedIds = computed<string[]>(() =>
    data.value?.active === true ? data.value.flagged_ids : [],
  )
  const lockedPreset = computed<PresetLockedInfo | null>(() =>
    data.value !== null && 'locked_preset' in data.value ? data.value.locked_preset : null,
  )
  const timeRemainingSeconds = computed<number | null>(() =>
    data.value?.active === true ? data.value.time_remaining_seconds : null,
  )

  function apply(next: SessionResponse): void {
    data.value = next
    error.value = null
  }

  function clear(): void {
    data.value = null
    error.value = null
  }

  async function fetchSession(query?: SessionQuery): Promise<SessionResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await sessionApi.getSession(query)
      apply(response)
      return response
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  async function start(body: StartRequest = {}): Promise<SessionResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await sessionApi.startSession(body)
      apply(response)
      return response
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  async function restore(sessionIdToRestore: string): Promise<SessionResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await sessionApi.restoreSession(sessionIdToRestore)
      apply(response)
      return response
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  async function next(): Promise<SessionResponse | null> {
    return runAction(actionsApi.actionNext)
  }

  async function prev(): Promise<SessionResponse | null> {
    return runAction(actionsApi.actionPrev)
  }

  async function jump(taskNum: number): Promise<SessionResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await actionsApi.actionJump(taskNum)
      apply(response)
      return response
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  async function flag(taskNum?: number): Promise<string[]> {
    error.value = null
    try {
      const response = await actionsApi.actionFlag(taskNum)
      if (data.value?.active === true) data.value.flagged_ids = response.flagged_ids
      return response.flagged_ids
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return []
    }
  }

  async function retry(): Promise<boolean> {
    error.value = null
    try {
      await actionsApi.actionRetry()
      return true
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return false
    }
  }

  async function submit(): Promise<SubmitResponse | null> {
    loading.value = true
    error.value = null
    try {
      const report = await actionsApi.actionSubmit()
      clear()
      sessionApi.persistCandidateToken(null)
      return report
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  async function runAction(
    action: () => Promise<SessionResponse>,
  ): Promise<SessionResponse | null> {
    loading.value = true
    error.value = null
    try {
      const response = await action()
      apply(response)
      return response
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return null
    } finally {
      loading.value = false
    }
  }

  async function reset(): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await sessionApi.resetSession()
      clear()
      sessionApi.persistCandidateToken(null)
      return true
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return false
    } finally {
      loading.value = false
    }
  }

  async function end(): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await sessionApi.endSession()
      clear()
      sessionApi.persistCandidateToken(null)
      return true
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : String(cause)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    data,
    loading,
    error,
    isActive,
    isInvited,
    isAdmin,
    isLocked,
    sessionId,
    currentTask,
    currentTaskNum,
    totalTasks,
    flaggedIds,
    lockedPreset,
    timeRemainingSeconds,
    apply,
    clear,
    fetchSession,
    start,
    restore,
    next,
    prev,
    jump,
    flag,
    retry,
    submit,
    reset,
    end,
  }
})
