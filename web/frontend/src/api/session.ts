import type { components } from './schema'
import { apiRequest } from './client'

export type SessionResponse = components['schemas']['SessionResponse']
export type SessionActive = components['schemas']['SessionActive']
export type SessionInactive = components['schemas']['SessionInactive']
export type SessionInvited = components['schemas']['SessionInvited']
export type TaskData = components['schemas']['TaskData']
export type PresetLockedInfo = components['schemas']['PresetLockedInfo']
export type StartRequest = components['schemas']['StartRequest']
export type StatusMessageResponse = components['schemas']['StatusMessageResponse']

export interface SessionQuery {
  admin?: boolean
  candidate?: boolean
  preset?: string
  token?: string
}

function toParams(query?: SessionQuery): Record<string, string | boolean | undefined> | undefined {
  if (!query) return undefined
  return {
    admin: query.admin,
    candidate: query.candidate,
    preset: query.preset,
    token: query.token,
  }
}

export function getSession(query?: SessionQuery): Promise<SessionResponse> {
  return apiRequest<SessionResponse>('/api/session', { query: toParams(query) })
}

export function startSession(body: StartRequest = {}): Promise<SessionResponse> {
  return apiRequest<SessionResponse>('/api/start', { method: 'POST', body })
}

export function restoreSession(sessionId: string): Promise<SessionResponse> {
  return apiRequest<SessionResponse>('/api/session/restore', {
    method: 'POST',
    body: { session_id: sessionId },
  })
}

export function resetSession(): Promise<StatusMessageResponse> {
  return apiRequest<StatusMessageResponse>('/api/reset', { method: 'POST' })
}

export function endSession(): Promise<StatusMessageResponse> {
  return apiRequest<StatusMessageResponse>('/api/end', { method: 'POST' })
}
