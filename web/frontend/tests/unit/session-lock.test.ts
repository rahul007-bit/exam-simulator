import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { SessionResponse } from '@/api/session'
import { useSessionStore } from '@/stores/session'

/**
 * Per-session owner lock: the SPA advertises a stable per-browser client id and
 * treats a `locked: true` inactive session as a normal (non-error) state.
 */

function clearCookies(): void {
  for (const entry of document.cookie.split(';')) {
    const name = entry.split('=')[0]?.trim()
    if (name) document.cookie = `${name}=; path=/; max-age=0`
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|;\\s*)${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

const LOCKED_SESSION = {
  active: false,
  session: null,
  locked: true,
  locked_preset: null,
  is_admin: false,
} as unknown as SessionResponse

const INACTIVE_SESSION = {
  active: false,
  session: null,
  locked_preset: null,
  is_admin: false,
} as unknown as SessionResponse

const ACTIVE_SESSION = {
  active: true,
  session_id: 'sess-1',
  name: 'Mock Exam',
  mode: 'practice',
  status: 'active',
  current_index: 0,
  total_tasks: 1,
  time_remaining_seconds: 60,
  created_at: '2026-01-01T00:00:00.000Z',
  server_timestamp: 0,
  flagged_ids: [],
  is_admin: false,
} as unknown as SessionResponse

describe('client id cookie', () => {
  beforeEach(() => {
    clearCookies()
    vi.resetModules()
  })

  afterEach(() => {
    clearCookies()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('creates and persists a cka_client_id cookie when absent', async () => {
    const client = await import('@/api/client')

    const id = client.getClientId()

    expect(id).toBeTruthy()
    expect(readCookie('cka_client_id')).toBe(id)
  })

  it('keeps an existing cka_client_id cookie stable across module reloads', async () => {
    document.cookie = 'cka_client_id=stable-id-123; path=/'

    const client = await import('@/api/client')

    expect(client.getClientId()).toBe('stable-id-123')
    expect(readCookie('cka_client_id')).toBe('stable-id-123')
  })

  it('sends X-Client-Id with credentials on every request', async () => {
    document.cookie = 'cka_client_id=header-id; path=/'
    const client = await import('@/api/client')
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: 'OK',
      text: () => Promise.resolve('{}'),
    })
    vi.stubGlobal('fetch', fetchMock)

    await client.apiRequest('/api/session')

    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect((init.headers as Record<string, string>)['X-Client-Id']).toBe('header-id')
    expect(init.credentials).toBe('include')
  })
})

describe('session store isLocked', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('is true only for the locked inactive payload', () => {
    const store = useSessionStore()

    store.apply(LOCKED_SESSION)

    expect(store.isLocked).toBe(true)
    expect(store.isActive).toBe(false)
  })

  it('is false for an ordinary inactive payload', () => {
    const store = useSessionStore()

    store.apply(INACTIVE_SESSION)

    expect(store.isLocked).toBe(false)
  })

  it('is false while a session is active', () => {
    const store = useSessionStore()

    store.apply(ACTIVE_SESSION)

    expect(store.isLocked).toBe(false)
    expect(store.isActive).toBe(true)
  })
})
