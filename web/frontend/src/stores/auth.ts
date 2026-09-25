import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as adminApi from '@/api/admin'
import * as authApi from '@/api/auth'
import { setAdminToken } from '@/api/client'

/**
 * Auth store (FE-030, extended for FS-002).
 *
 * Wraps the user auth endpoints (`/api/auth/login`, `/api/auth/me`,
 * `/api/auth/logout`) and keeps the legacy admin endpoints
 * (`/api/admin/login`, `/api/admin/check`, `/api/admin/logout`) working so the
 * admin cookie/bearer flow and existing FE-030 callers are unaffected.
 *
 * The API client already sends `credentials: 'include'` so the httpOnly
 * `cka_auth_token` / `admin_token` cookies travel with every request; the bearer
 * token returned by the legacy `/api/admin/login` is additionally attached to
 * the client for the lifetime of the tab so either credential source works.
 *
 * Roles are modelled as a list so the route guard can gate `meta.roles` for the
 * user/admin scope.
 */
export const ADMIN_ROLE = 'admin'
export const USER_ROLE = 'user'

export interface AuthState {
  authenticated: boolean
  roles: string[]
  username: string | null
}

export const useAuthStore = defineStore('auth', () => {
  const authenticated = ref(false)
  const roles = ref<string[]>([])
  const username = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  /** True once a login attempt or a session check has resolved. */
  const initialized = ref(false)

  const isAuthenticated = computed(() => authenticated.value)
  const isAdmin = computed(() => roles.value.includes(ADMIN_ROLE))

  function clearSession(): void {
    authenticated.value = false
    roles.value = []
    username.value = null
    setAdminToken(null)
  }

  function applySession(value: boolean, nextRoles: string[], nextUsername: string | null): void {
    authenticated.value = value
    roles.value = value ? nextRoles : []
    username.value = value ? nextUsername : null
    if (!value) setAdminToken(null)
  }

  function applyAuthenticated(value: boolean): void {
    applySession(value, value ? [ADMIN_ROLE] : [], null)
  }

  function message(cause: unknown): string {
    return cause instanceof Error ? cause.message : String(cause)
  }

  /** User/password sign-in via `/api/auth/login` (FS-002). */
  async function login(usernameInput: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      const response = await authApi.authLogin(usernameInput, password)
      applySession(true, response.role ? [response.role] : [], response.username ?? usernameInput)
      return true
    } catch (cause) {
      clearSession()
      error.value = message(cause)
      return false
    } finally {
      initialized.value = true
      loading.value = false
    }
  }

  /** Legacy admin-password sign-in via `/api/admin/login` (FE-030). */
  async function loginAdmin(password: string): Promise<boolean> {
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

  /**
   * Resolves the session, preferring the user cookie via `/api/auth/me` and
   * falling back to the legacy `/api/admin/check` (admin cookie/bearer).
   */
  async function check(): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      try {
        const me = await authApi.authMe()
        if (me.authenticated) {
          applySession(true, me.role ? [me.role] : [], me.username)
          return true
        }
      } catch {
        /* unauthenticated user session (401) — fall through to the admin check */
      }

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

  /** Clears both the user and legacy admin sessions defensively. */
  async function logout(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const results = await Promise.allSettled([authApi.authLogout(), adminApi.adminLogout()])
      const rejected = results.find((result) => result.status === 'rejected')
      if (rejected && rejected.status === 'rejected') error.value = message(rejected.reason)
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
    username,
    loading,
    error,
    initialized,
    isAuthenticated,
    isAdmin,
    login,
    loginAdmin,
    check,
    logout,
    hasRole,
    hasAnyRole,
  }
})
