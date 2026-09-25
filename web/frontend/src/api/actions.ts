import type { components } from './schema'
import { apiRequest } from './client'
import type { SessionResponse } from './session'

export type JumpRequest = components['schemas']['JumpRequest']
export type FlagRequest = components['schemas']['FlagRequest']
export type FlagResponse = components['schemas']['FlagResponse']
export type SubmitResponse = components['schemas']['SubmitResponse']
export type ScorecardRow = components['schemas']['ScorecardRow']
export type StatusMessageResponse = components['schemas']['StatusMessageResponse']

export function actionNext(): Promise<SessionResponse> {
  return apiRequest<SessionResponse>('/api/action/next', { method: 'POST' })
}

export function actionPrev(): Promise<SessionResponse> {
  return apiRequest<SessionResponse>('/api/action/prev', { method: 'POST' })
}

export function actionJump(taskNum: number): Promise<SessionResponse> {
  const body: JumpRequest = { task_num: taskNum }
  return apiRequest<SessionResponse>('/api/action/jump', { method: 'POST', body })
}

export function actionFlag(taskNum?: number): Promise<FlagResponse> {
  const body: FlagRequest = taskNum === undefined ? {} : { task_num: taskNum }
  return apiRequest<FlagResponse>('/api/action/flag', { method: 'POST', body })
}

export function actionRetry(): Promise<StatusMessageResponse> {
  return apiRequest<StatusMessageResponse>('/api/action/retry', { method: 'POST' })
}

export function actionSubmit(): Promise<SubmitResponse> {
  return apiRequest<SubmitResponse>('/api/action/submit', { method: 'POST' })
}
