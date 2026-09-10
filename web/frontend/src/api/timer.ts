import type { components } from './schema'
import { apiRequest } from './client'

export type TimerResponse = components['schemas']['TimerResponse']

/** Shape of the `timer_tick` WS payload (PLAN.md §3 WS contracts). */
export interface TimerTick {
  time_remaining_seconds?: number | null
  time_limit_minutes?: number | null
  server_timestamp?: number
  start_timestamp?: number
  end_timestamp?: number
  total_seconds?: number
  elapsed_seconds?: number
}

export function getTimer(): Promise<TimerResponse> {
  return apiRequest<TimerResponse>('/api/timer')
}
