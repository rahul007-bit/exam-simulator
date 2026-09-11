import type { Pinia } from 'pinia'

import { readCandidateToken } from '@/api/session'
import { useSessionStore } from './session'
import { useTimerStore } from './timer'

export { useSessionStore } from './session'
export { useTimerStore, formatDuration } from './timer'
export { usePresetsStore } from './presets'

/**
 * Minimal app bootstrap: hydrate the session + timer stores from the backend.
 *
 * Kept out of components so the stores remain independently testable; failures
 * are captured in each store's `error` state rather than throwing.
 */
export async function initAppStores(pinia?: Pinia): Promise<void> {
  const session = useSessionStore(pinia)
  const timer = useTimerStore(pinia)

  // Resume an invited/candidate session by its persisted token so a refresh
  // re-attaches to the same session instead of the global one.
  const token = readCandidateToken()
  await Promise.allSettled([
    session.fetchSession(token ? { token } : undefined),
    timer.fetchTimer(),
  ])

  if (session.data) timer.syncFromSession(session.data)
}
