import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { getAdminToken, setAdminToken } from '@/api/client'
import { ADMIN_ROLE, useAuthStore } from '@/stores/auth'
import router, { authGuard } from '@/router'
import { clear as clearToasts } from '@/composables/useToast'
import type { RouteLocationNormalized } from 'vue-router'

function jsonResponse(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    text: () => Promise.resolve(JSON.stringify(payload)),
  } as unknown as Response
}

function routeAt(meta: RouteLocationNormalized['meta'], fullPath = '/admin') {
  return { meta, fullPath } as unknown as RouteLocationNormalized
}

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  setActivePinia(createPinia())
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
  setAdminToken(null)
  clearToasts()
})

afterEach(() => {
  vi.unstubAllGlobals()
  setAdminToken(null)
})

describe('auth store (FE-030)', () => {
  it('logs in with the correct request and stores the bearer token', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ status: 'ok', token: 'tok-123', authenticated: true }),
    )
    const auth = useAuthStore()

    const ok = await auth.login('secret')

    expect(ok).toBe(true)
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.isAdmin).toBe(true)
    expect(auth.initialized).toBe(true)
    expect(auth.error).toBeNull()
    expect(getAdminToken()).toBe('tok-123')

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/admin/login')
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ password: 'secret' }))
    expect(init.credentials).toBe('include')
  })

  it('reports a failed login without authenticating', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'Invalid admin password' }, 401))
    const auth = useAuthStore()

    const ok = await auth.login('wrong')

    expect(ok).toBe(false)
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.isAdmin).toBe(false)
    expect(auth.error).toBe('Invalid admin password')
    expect(getAdminToken()).toBeNull()
  })

  it('checks the session via the cookie and records authentication', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ authenticated: true }))
    const auth = useAuthStore()

    const ok = await auth.check()

    expect(ok).toBe(true)
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.initialized).toBe(true)

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/admin/check')
    expect(init.credentials).toBe('include')
  })

  it('clears the bearer token when /api/admin/check is unauthenticated', async () => {
    setAdminToken('stale-token')
    fetchMock.mockResolvedValueOnce(jsonResponse({ authenticated: false }))
    const auth = useAuthStore()

    const ok = await auth.check()

    expect(ok).toBe(false)
    expect(auth.isAuthenticated).toBe(false)
    expect(getAdminToken()).toBeNull()
  })

  it('logs out and clears local session state', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ status: 'ok', token: 'tok-1', authenticated: true }),
    )
    const auth = useAuthStore()
    await auth.login('secret')
    expect(auth.isAuthenticated).toBe(true)

    fetchMock.mockResolvedValueOnce(jsonResponse({ status: 'ok', authenticated: false }))
    await auth.logout()

    expect(auth.isAuthenticated).toBe(false)
    expect(auth.roles).toEqual([])
    expect(getAdminToken()).toBeNull()
    const [url, init] = fetchMock.mock.calls[1] as [string, RequestInit]
    expect(url).toBe('/api/admin/logout')
    expect(init.method).toBe('POST')
  })

  it('still clears local session state when the logout request fails', async () => {
    setAdminToken('tok-1')
    fetchMock.mockRejectedValueOnce(new Error('network down'))
    const auth = useAuthStore()
    auth.$patch({ authenticated: true, roles: [ADMIN_ROLE] })

    await auth.logout()

    expect(auth.isAuthenticated).toBe(false)
    expect(getAdminToken()).toBeNull()
    expect(auth.error).toBe('network down')
  })

  it('evaluates role membership for future FS-002 guards', () => {
    const auth = useAuthStore()
    expect(auth.hasRole(ADMIN_ROLE)).toBe(false)
    expect(auth.hasAnyRole([])).toBe(true)

    auth.$patch({ authenticated: true, roles: [ADMIN_ROLE] })

    expect(auth.hasRole(ADMIN_ROLE)).toBe(true)
    expect(auth.hasAnyRole(['admin', 'proctor'])).toBe(true)
    expect(auth.hasAnyRole(['proctor'])).toBe(false)
  })
})

describe('auth route guard (FE-030)', () => {
  it('redirects unauthenticated /admin to /login with the intended path', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ authenticated: false }))
    setActivePinia(createPinia())

    const result = await authGuard(routeAt({ requiresAuth: true, roles: ['admin'] }))

    expect(result).toEqual({ name: 'login', query: { redirect: '/admin' } })
    expect(fetchMock).toHaveBeenCalledWith('/api/admin/check', expect.objectContaining({}))
  })

  it('allows an authenticated admin through', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ authenticated: true }))
    setActivePinia(createPinia())

    const result = await authGuard(routeAt({ requiresAuth: true, roles: ['admin'] }))

    expect(result).toBe(true)
  })

  it('leaves public routes untouched without probing the backend', async () => {
    setActivePinia(createPinia())

    const result = await authGuard(routeAt({}, '/'))

    expect(result).toBe(true)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('redirects via the router to /login for unauthenticated /admin', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ authenticated: false }))
    setActivePinia(createPinia())

    await router.push('/admin')

    expect(router.currentRoute.value.name).toBe('login')
    expect(router.currentRoute.value.query.redirect).toBe('/admin')
  })

  it('navigates to /admin once authenticated', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ authenticated: true }))
    setActivePinia(createPinia())

    await router.push('/admin')

    expect(router.currentRoute.value.name).toBe('admin')
  })
})
