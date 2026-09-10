import type { Pinia } from 'pinia'

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

  await Promise.allSettled([session.fetchSession(), timer.fetchTimer()])

  if (session.data) timer.syncFromSession(session.data)
}
