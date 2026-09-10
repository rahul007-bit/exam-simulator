import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useSessionStore } from '@/stores/session'
import { useTimerStore } from '@/stores/timer'
import { usePresetsStore } from '@/stores/presets'
import type { SessionActive } from '@/api/session'

const SESSION: SessionActive = {
  active: true,
  session_id: 'sess-1',
  candidate_token: 'tok-1',
  name: 'Mock Exam 01',
  mode: 'sequential',
  status: 'active',
  current_index: 0,
  total_tasks: 17,
  time_limit_minutes: 120,
  time_remaining_seconds: 7200,
  created_at: '2026-09-10T00:00:00+00:00',
  start_timestamp: 1757462400,
  end_timestamp: 1757469600,
  server_timestamp: 1757462400,
  flagged_ids: [],
  current_task: {
    task_num: 1,
    id: 'TR-001',
    title: 'CrashLoopBackOff on Checkout',
    domain: 'troubleshooting',
    difficulty: 'medium',
    points: 4,
    target_context: 'k3d-cka',
    namespace: 'checkout',
    description: '...',
    cluster_scoped: false,
    tags: ['pods'],
    is_flagged: false,
  },
  terminal_port: '7681',
  novnc_port: '6080',
  is_admin: false,
}

function jsonResponse(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    text: () => Promise.resolve(JSON.stringify(payload)),
  } as unknown as Response
}

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  setActivePinia(createPinia())
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('session store (FE-004 T2)', () => {
  it('populates typed /api/session data', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(SESSION))
    const store = useSessionStore()

    const result = await store.fetchSession()

    expect(result).toEqual(SESSION)
    expect(store.isActive).toBe(true)
    expect(store.isAdmin).toBe(false)
    expect(store.sessionId).toBe('sess-1')
    expect(store.totalTasks).toBe(17)
    expect(store.currentTaskNum).toBe(1)
    expect(store.currentTask?.id).toBe('TR-001')
    expect(store.error).toBeNull()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/session',
      expect.objectContaining({ method: 'GET', credentials: 'include' }),
    )
  })

  it('builds session query params from typed options', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(SESSION))
    const store = useSessionStore()

    await store.fetchSession({ token: 'tok-1', admin: true })

    const url = fetchMock.mock.calls[0][0] as string
    const params = new URLSearchParams(url.split('?')[1])
    expect(url.startsWith('/api/session?')).toBe(true)
    expect(params.get('token')).toBe('tok-1')
    expect(params.get('admin')).toBe('true')
  })

  it('surfaces API errors without throwing', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'No active exam session' }, 400))
    const store = useSessionStore()

    const result = await store.fetchSession()

    expect(result).toBeNull()
    expect(store.error).toBe('No active exam session')
  })

  it('applies action results and toggles flags', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(SESSION))
    const store = useSessionStore()
    await store.fetchSession()

    fetchMock.mockResolvedValueOnce(
      jsonResponse({ id: 'TR-001', task_num: 1, is_flagged: true, flagged_ids: ['TR-001'] }),
    )
    const flagged = await store.flag()

    expect(flagged).toEqual(['TR-001'])
    expect(store.flaggedIds).toEqual(['TR-001'])
  })

  it('submits and clears the session on the scorecard report', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(SESSION))
    const store = useSessionStore()
    await store.fetchSession()

    const report = {
      scorecard: [],
      total_earned: 10,
      total_possible: 20,
      percentage: 50,
      passed: false,
      threshold: 66,
      session_id: 'sess-1',
      exam_name: 'Mock Exam 01',
      submitted_at: '2026-09-10T01:00:00+00:00',
    }
    fetchMock.mockResolvedValueOnce(jsonResponse(report))
    const result = await store.submit()

    expect(result?.percentage).toBe(50)
    expect(store.isActive).toBe(false)
    expect(store.data).toBeNull()
  })
})

describe('timer store (FE-004)', () => {
  it('syncs from the session payload and formats the countdown', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(SESSION))
    const session = useSessionStore()
    await session.fetchSession()

    const timer = useTimerStore()
    timer.syncFromSession(session.data as SessionActive)

    expect(timer.active).toBe(true)
    expect(timer.remainingSeconds).toBe(7200)
    expect(timer.formatted).toBe('2:00:00')
    expect(timer.urgency).toBe('normal')
  })

  it('applies a timer_tick payload and computes urgency', () => {
    const timer = useTimerStore()
    timer.applyTick({ time_remaining_seconds: 120, server_timestamp: 1 })

    expect(timer.remainingSeconds).toBe(120)
    expect(timer.formatted).toBe('02:00')
    expect(timer.urgency).toBe('critical')
    expect(timer.isExpired).toBe(false)
  })

  it('fetches /api/timer and marks expiry', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ active: true, time_remaining_seconds: 0, time_limit_minutes: 120 }),
    )
    const timer = useTimerStore()
    await timer.fetchTimer()

    expect(timer.isExpired).toBe(true)
  })
})

describe('presets store (FE-004)', () => {
  it('loads the preset catalog and selection', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        presets: [
          { filename: 'mock-01-acme', name: 'Mock Exam 01', questions: ['TR-001'], task_count: 1 },
        ],
        selected: 'mock-01-acme',
      }),
    )
    const store = usePresetsStore()

    const presets = await store.fetchPresets()

    expect(presets).toHaveLength(1)
    expect(store.selected).toBe('mock-01-acme')
    expect(store.selectedPreset?.name).toBe('Mock Exam 01')
  })

  it('selects a preset via POST', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        status: 'ok',
        preset: 'mock-02-globex',
        info: {
          filename: 'mock-02-globex',
          name: 'Globex',
          description: '',
          task_count: 17,
          time_limit_minutes: 120,
          pass_threshold_percent: 66,
        },
      }),
    )
    const store = usePresetsStore()

    await store.selectPreset('mock-02-globex')

    expect(store.selected).toBe('mock-02-globex')
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.method).toBe('POST')
    expect(init.body).toBe(JSON.stringify({ preset: 'mock-02-globex' }))
  })
})
