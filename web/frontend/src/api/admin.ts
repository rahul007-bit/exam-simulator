import type { components } from './schema'
import { apiRequest } from './client'

export type AdminLoginRequest = components['schemas']['AdminLoginRequest']
export type AdminLoginResponse = components['schemas']['AdminLoginResponse']
export type AdminCheckResponse = components['schemas']['AdminCheckResponse']
export type AdminLogoutResponse = components['schemas']['AdminLogoutResponse']
export type AdminConfigRequest = components['schemas']['AdminConfigRequest']
export type AdminConfigResponse = components['schemas']['AdminConfigResponse']
export type AdminSetConfigResponse = components['schemas']['AdminSetConfigResponse']
export type ResourceInfo = components['schemas']['ResourceInfo']
export type SetResourceLimitRequest = components['schemas']['SetResourceLimitRequest']
export type CreateSessionInviteRequest = components['schemas']['CreateSessionInviteRequest']
export type CreateSessionInviteResponse = components['schemas']['CreateSessionInviteResponse']
export type AdminSessionsResponse = components['schemas']['AdminSessionsResponse']
export type AdminSessionItem = components['schemas']['AdminSessionItem']

export function adminLogin(password: string): Promise<AdminLoginResponse> {
  const body: AdminLoginRequest = { password }
  return apiRequest<AdminLoginResponse>('/api/admin/login', { method: 'POST', body })
}

export function adminCheck(): Promise<AdminCheckResponse> {
  return apiRequest<AdminCheckResponse>('/api/admin/check')
}

export function adminLogout(): Promise<AdminLogoutResponse> {
  return apiRequest<AdminLogoutResponse>('/api/admin/logout', { method: 'POST' })
}

export function getAdminConfig(): Promise<AdminConfigResponse> {
  return apiRequest<AdminConfigResponse>('/api/admin/config')
}

export function setAdminConfig(defaultPreset: string): Promise<AdminSetConfigResponse> {
  const body: AdminConfigRequest = { default_preset: defaultPreset }
  return apiRequest<AdminSetConfigResponse>('/api/admin/config', { method: 'POST', body })
}

export function getAdminResources(): Promise<ResourceInfo> {
  return apiRequest<ResourceInfo>('/api/admin/resources')
}

export function setAdminResources(maxConcurrentSessions: number): Promise<ResourceInfo> {
  const body: SetResourceLimitRequest = { max_concurrent_sessions: maxConcurrentSessions }
  return apiRequest<ResourceInfo>('/api/admin/resources', { method: 'POST', body })
}

export function createSessionInvite(preset?: string): Promise<CreateSessionInviteResponse> {
  const body: CreateSessionInviteRequest = preset === undefined ? {} : { preset }
  return apiRequest<CreateSessionInviteResponse>('/api/admin/sessions/create', {
    method: 'POST',
    body,
  })
}

export function listAdminSessions(): Promise<AdminSessionsResponse> {
  return apiRequest<AdminSessionsResponse>('/api/admin/sessions')
}
