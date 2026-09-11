import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createUser, deleteUser, listUsers } from '@/api/users'
import type { User } from '@/api/users'
import AdminUsersPanel from '@/components/admin/AdminUsersPanel.vue'
import { useAuthStore } from '@/stores/auth'

const mocks = vi.hoisted(() => ({ confirm: vi.fn(), push: vi.fn() }))

vi.mock('@/api/users', () => ({
  listUsers: vi.fn(),
  createUser: vi.fn(),
  deleteUser: vi.fn(),
}))
vi.mock('@/composables/useConfirm', () => ({ useConfirm: () => ({ confirm: mocks.confirm }) }))
vi.mock('@/composables/useToast', () => ({ useToast: () => ({ push: mocks.push }) }))

const listUsersMock = vi.mocked(listUsers)
const createUserMock = vi.mocked(createUser)
const deleteUserMock = vi.mocked(deleteUser)

const ROOT: User = { username: 'root', role: 'admin', created_at: '2024-01-01T00:00:00Z' }
const ALICE: User = { username: 'alice', role: 'user', created_at: '2024-02-01T00:00:00Z' }

let pinia: ReturnType<typeof createPinia>

function mountPanel() {
  return mount(AdminUsersPanel, { global: { plugins: [pinia] } })
}

beforeEach(() => {
  pinia = createPinia()
  setActivePinia(pinia)
  vi.clearAllMocks()
  mocks.confirm.mockResolvedValue(true)
  const auth = useAuthStore()
  auth.$patch({ authenticated: true, roles: ['admin'], username: 'root' })
})

describe('AdminUsersPanel', () => {
  it('renders the user list', async () => {
    listUsersMock.mockResolvedValueOnce({ users: [ROOT, ALICE], total: 2 })

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.findAll('[data-testid="users-row"]')).toHaveLength(2)
    expect(wrapper.text()).toContain('root')
    expect(wrapper.text()).toContain('alice')
    wrapper.unmount()
  })

  it('creates a user with the default role', async () => {
    listUsersMock.mockResolvedValueOnce({ users: [ROOT], total: 1 })
    createUserMock.mockResolvedValueOnce({
      status: 'ok',
      user: ALICE,
    })

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.get('[data-testid="users-username"] input').setValue('alice')
    await wrapper.get('[data-testid="users-password"] input').setValue('secret')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createUserMock).toHaveBeenCalledWith('alice', 'secret', 'user')
    expect(wrapper.findAll('[data-testid="users-row"]')).toHaveLength(2)
    wrapper.unmount()
  })

  it('allows creating an admin user', async () => {
    listUsersMock.mockResolvedValueOnce({ users: [ROOT], total: 1 })
    createUserMock.mockResolvedValueOnce({ status: 'ok', user: { ...ALICE, role: 'admin' } })

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.get('[data-testid="users-role"]').trigger('click')
    await flushPromises()
    const options = wrapper.findAll('[role="option"]')
    await options[options.length - 1].trigger('click')
    await flushPromises()

    await wrapper.get('[data-testid="users-username"] input').setValue('bob')
    await wrapper.get('[data-testid="users-password"] input').setValue('pw')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createUserMock).toHaveBeenCalledWith('bob', 'pw', 'admin')
    wrapper.unmount()
  })

  it('deletes a user only after confirmation', async () => {
    listUsersMock.mockResolvedValueOnce({ users: [ROOT, ALICE], total: 2 })
    deleteUserMock.mockResolvedValueOnce({ status: 'ok', username: 'alice' })

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.get('[data-testid="users-delete-alice"]').trigger('click')
    await flushPromises()

    expect(mocks.confirm).toHaveBeenCalledTimes(1)
    expect(deleteUserMock).toHaveBeenCalledWith('alice')
    expect(wrapper.findAll('[data-testid="users-row"]')).toHaveLength(1)
    wrapper.unmount()
  })

  it('does not delete when confirmation is declined', async () => {
    mocks.confirm.mockResolvedValueOnce(false)
    listUsersMock.mockResolvedValueOnce({ users: [ROOT, ALICE], total: 2 })

    const wrapper = mountPanel()
    await flushPromises()
    await wrapper.get('[data-testid="users-delete-alice"]').trigger('click')
    await flushPromises()

    expect(deleteUserMock).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('blocks deleting the last admin and your own account', async () => {
    listUsersMock.mockResolvedValueOnce({ users: [ROOT], total: 1 })

    const wrapper = mountPanel()
    await flushPromises()

    const button = wrapper.get('[data-testid="users-delete-root"]')
    expect(button.attributes('disabled')).toBeDefined()
    wrapper.unmount()
  })
})
