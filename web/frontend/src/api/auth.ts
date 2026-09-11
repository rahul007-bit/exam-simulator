import type { components } from './schema'
import { apiRequest } from './client'

export type LoginRequest = components['schemas']['LoginRequest']
export type LoginResponse = components['schemas']['LoginResponse']
export type AuthLogoutResponse = components['schemas']['AuthLogoutResponse']
export type AuthMeResponse = components['schemas']['AuthMeResponse']

export function authLogin(username: string, password: string): Promise<LoginResponse> {
  const body: LoginRequest = { username, password }
  return apiRequest<LoginResponse>('/api/auth/login', { method: 'POST', body })
}

export function authLogout(): Promise<AuthLogoutResponse> {
  return apiRequest<AuthLogoutResponse>('/api/auth/logout', { method: 'POST' })
}

export function authMe(): Promise<AuthMeResponse> {
  return apiRequest<AuthMeResponse>('/api/auth/me')
}
