import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as adminApi from '@/api/admin'
import { setAdminToken } from '@/api/client'

/**
 * Auth store (FE-030).
 *
 * Wraps the admin auth endpoints (`/api/admin/login`, `/api/admin/check`,
 * `/api/admin/logout`). The API client already sends `credentials: 'include'`
 * so the httpOnly `admin_token` cookie travels with every request; the bearer
 * token returned by `/api/admin/login` is additionally attached to the client
 * for the lifetime of the tab so either credential source works.
 *
 * Roles are modelled as a set so the route guard can be generalised now for the
 * future FS-002 user/admin scope (`meta: { requiresAuth, roles }`).
 */
export const ADMIN_ROLE = 'admin'

export interface AuthState {
  authenticated: boolean
  roles: string[]
}

export const useAuthStore = defineStore('auth', () => {
  const authenticated = ref(false)
  const roles = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  /** True once a login attempt or `/api/admin/check` has resolved. */
  const initialized = ref(false)

  const isAuthenticated = computed(() => authenticated.value)
  const isAdmin = computed(() => roles.value.includes(ADMIN_ROLE))

  function clearSession(): void {
    authenticated.value = false
    roles.value = []
    setAdminToken(null)
  }

  function applyAuthenticated(value: boolean): void {
    authenticated.value = value
    roles.value = value ? [ADMIN_ROLE] : []
    if (!value) setAdminToken(null)
  }

  function message(cause: unknown): string {
    return cause instanceof Error ? cause.message : String(cause)
  }

  async function login(password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const response = await adminApi.adminLogin(password)
      applyAuthenticated(response.authenticated)
      if (response.authenticated && response.token) setAdminToken(response.token)
      return response.authenticated
    } catch (cause) {
      clearSession()
      error.value = message(cause)
      return false
    } finally {
      initialized.value = true
      loading.value = false
    }
  }

  async function check(): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const response = await adminApi.adminCheck()
      applyAuthenticated(response.authenticated)
      return response.authenticated
    } catch (cause) {
      clearSession()
      error.value = message(cause)
      return false
    } finally {
      initialized.value = true
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await adminApi.adminLogout()
    } catch (cause) {
      error.value = message(cause)
    } finally {
      clearSession()
      initialized.value = true
      loading.value = false
    }
  }

  function hasRole(role: string): boolean {
    return roles.value.includes(role)
  }

  function hasAnyRole(required: readonly string[]): boolean {
    return required.length === 0 || required.some((role) => roles.value.includes(role))
  }

  return {
    authenticated,
    roles,
    loading,
    error,
    initialized,
    isAuthenticated,
    isAdmin,
    login,
    check,
    logout,
    hasRole,
    hasAnyRole,
  }
})
