import type { components } from './schema'
import { apiRequest } from './client'

export type SessionActive = components['schemas']['SessionActive']
// The inactive payload is hand-augmented with the per-session owner lock flag
// (`locked: true` means another client/device owns the active session). A locked
// session is not an error — it is a normal HTTP 200 status.
export type SessionInactive = components['schemas']['SessionInactive'] & {
  locked?: boolean
}
export type SessionInvited = components['schemas']['SessionInvited']
export type SessionResponse = SessionActive | SessionInactive | SessionInvited
export type TaskData = components['schemas']['TaskData']
export type PresetLockedInfo = components['schemas']['PresetLockedInfo']

/** localStorage key holding the candidate token used to resume a session. */
export const CANDIDATE_TOKEN_KEY = 'cka:candidate-token'

export function readCandidateToken(): string | null {
  if (typeof localStorage === 'undefined') return null
  return localStorage.getItem(CANDIDATE_TOKEN_KEY)
}

export function persistCandidateToken(token: string | null): void {
  if (typeof localStorage === 'undefined') return
  if (token) localStorage.setItem(CANDIDATE_TOKEN_KEY, token)
  else localStorage.removeItem(CANDIDATE_TOKEN_KEY)
}
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
