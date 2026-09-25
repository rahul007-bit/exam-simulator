import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { listMyAssignments } from '@/api/assignments'
import type { Assignment } from '@/api/assignments'
import { generatePreset, getPresets, selectPreset } from '@/api/presets'
import { useAuthStore } from '@/stores/auth'
import DashboardView from '@/views/DashboardView.vue'

/**
 * FS-005 — the user dashboard must list only the signed-in user's assignments
 * (`GET /api/assignments`) and must never touch the preset/question catalog.
 * "Start" extracts the invitation token from the assignment URL and navigates
 * the candidate route to `/?token=<token>`.
 */

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  session: { isActive: false, fetchSession: vi.fn() },
}))

vi.mock('vue-router', () => ({ useRouter: () => ({ push: mocks.push }) }))
vi.mock('@/api/assignments', () => ({ listMyAssignments: vi.fn() }))
vi.mock('@/api/presets', () => ({
  getPresets: vi.fn(),
  selectPreset: vi.fn(),
  generatePreset: vi.fn(),
}))
vi.mock('@/stores/session', () => ({ useSessionStore: () => mocks.session }))

const listMyAssignmentsMock = vi.mocked(listMyAssignments)
const getPresetsMock = vi.mocked(getPresets)
const selectPresetMock = vi.mocked(selectPreset)
const generatePresetMock = vi.mocked(generatePreset)

const NETWORK = vi.fn()

const PENDING: Assignment = {
  id: 'assign-1',
  username: 'alice',
  preset: 'mock-01-acme',
  assigned_by: 'admin',
  status: 'pending',
  created_at: '2024-06-15T12:00:00Z',
  url: '/?token=tok-123',
}

const STARTED: Assignment = {
  ...PENDING,
  id: 'assign-2',
  status: 'started',
  url: '/?token=tok-456',
}
const EXPIRED: Assignment = {
  ...PENDING,
  id: 'assign-3',
  status: 'expired',
  url: '/?token=tok-789',
}

let pinia: ReturnType<typeof createPinia>

function signIn(): void {
  const auth = useAuthStore()
  auth.$patch({ authenticated: true, roles: ['user'], username: 'alice' })
}

function mountView() {
  return mount(DashboardView, { global: { plugins: [pinia] } })
}

beforeEach(() => {
  pinia = createPinia()
  setActivePinia(pinia)
  vi.clearAllMocks()
  mocks.session.isActive = false
  vi.stubGlobal('fetch', NETWORK)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('DashboardView (FS-005)', () => {
  it('renders the signed-in user assignments without calling the catalog', async () => {
    signIn()
    listMyAssignmentsMock.mockResolvedValueOnce({ assignments: [PENDING], total: 1 })

    const wrapper = mountView()
    await flushPromises()

    expect(listMyAssignmentsMock).toHaveBeenCalledTimes(1)
    expect(wrapper.findAll('[data-testid="dashboard-row"]')).toHaveLength(1)
    expect(wrapper.get('[data-testid="dashboard-row"]').text()).toContain('mock-01-acme')
    expect(wrapper.get('[data-testid="dashboard-row"]').text()).toContain('Pending')
    expect(wrapper.get('[data-testid="dashboard-row"]').text()).toContain('2024')
    expect(wrapper.get('[data-testid="dashboard-row"]').text()).toContain('Start')

    expect(getPresetsMock).not.toHaveBeenCalled()
    expect(selectPresetMock).not.toHaveBeenCalled()
    expect(generatePresetMock).not.toHaveBeenCalled()
    expect(NETWORK).not.toHaveBeenCalled()

    wrapper.unmount()
  })

  it('shows the empty state when there are no assignments', async () => {
    signIn()
    listMyAssignmentsMock.mockResolvedValueOnce({ assignments: [], total: 0 })

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.get('[data-testid="dashboard-empty"]').text()).toContain('No assigned exams yet')
    expect(wrapper.find('[data-testid="dashboard-row"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('start navigates to the candidate route with the token from the assignment URL', async () => {
    signIn()
    listMyAssignmentsMock.mockResolvedValueOnce({ assignments: [PENDING], total: 1 })

    const wrapper = mountView()
    await flushPromises()
    await wrapper.get(`[data-testid="dashboard-start-${PENDING.id}"]`).trigger('click')

    expect(mocks.push).toHaveBeenCalledTimes(1)
    expect(mocks.push).toHaveBeenCalledWith({ path: '/', query: { token: 'tok-123' } })
    wrapper.unmount()
  })

  it('extracts the token from an absolute assignment URL', async () => {
    signIn()
    const absolute: Assignment = { ...PENDING, url: 'https://exam.example.com/?token=abs-9' }
    listMyAssignmentsMock.mockResolvedValueOnce({ assignments: [absolute], total: 1 })

    const wrapper = mountView()
    await flushPromises()
    await wrapper.get(`[data-testid="dashboard-start-${absolute.id}"]`).trigger('click')

    expect(mocks.push).toHaveBeenCalledWith({ path: '/', query: { token: 'abs-9' } })
    wrapper.unmount()
  })

  it('offers Resume for started assignments and hides Start for expired ones', async () => {
    signIn()
    listMyAssignmentsMock.mockResolvedValueOnce({ assignments: [STARTED, EXPIRED], total: 2 })

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('Resume')
    expect(wrapper.text()).toContain('Expired')
    expect(wrapper.find('[data-testid="dashboard-unavailable"]').exists()).toBe(true)
    expect(wrapper.find(`[data-testid="dashboard-start-${EXPIRED.id}"]`).exists()).toBe(false)
    wrapper.unmount()
  })

  it('renders an error state when the assignments request fails', async () => {
    signIn()
    listMyAssignmentsMock.mockRejectedValueOnce(new Error('Network down'))

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.get('[data-testid="dashboard-error"]').text()).toContain('Network down')
    expect(wrapper.get('[role="alert"]').text()).toContain('Network down')
    expect(wrapper.find('[data-testid="dashboard-row"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('re-fetches the user assignments when Refresh is pressed', async () => {
    signIn()
    listMyAssignmentsMock.mockResolvedValue({ assignments: [PENDING], total: 1 })

    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('[data-testid="dashboard-refresh"]').trigger('click')
    await flushPromises()

    expect(listMyAssignmentsMock).toHaveBeenCalledTimes(2)
    expect(NETWORK).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('redirects to login when the session is not authenticated', async () => {
    const auth = useAuthStore()
    const check = vi.spyOn(auth, 'check').mockResolvedValue(false)

    const wrapper = mountView()
    await flushPromises()

    expect(check).toHaveBeenCalledTimes(1)
    expect(listMyAssignmentsMock).not.toHaveBeenCalled()
    expect(mocks.push).toHaveBeenCalledWith({
      name: 'login',
      query: { redirect: '/assignments' },
    })
    wrapper.unmount()
  })

  it('hides the custom-exam builder while an exam is active', async () => {
    signIn()
    mocks.session.isActive = true
    listMyAssignmentsMock.mockResolvedValueOnce({ assignments: [], total: 0 })

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).not.toContain('Custom exam')
    wrapper.unmount()
  })
})
