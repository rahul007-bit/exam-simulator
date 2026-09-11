import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { createSessionInvite } from '@/api/admin'
import type { CreateSessionInviteResponse } from '@/api/admin'
import { ApiError } from '@/api/client'
import AdminInviteForm from '@/components/admin/AdminInviteForm.vue'
import type { SelectOption } from '@/components/ui'
import {
  absoluteInviteUrl,
  buildInviteUrl,
  copyTextToClipboard,
  useAdminInvites,
} from '@/composables/useAdminInvites'

vi.mock('@/api/admin', () => ({
  createSessionInvite: vi.fn(),
}))

// Headless UI observes its popper/panel with ResizeObserver and scrolls the
// active option into view; jsdom implements neither.
if (!('ResizeObserver' in globalThis)) {
  class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver = ResizeObserverStub
}
if (!Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}

const createSessionInviteMock = vi.mocked(createSessionInvite)

const INVITE: CreateSessionInviteResponse = {
  token: 'tok-abc',
  preset: 'mock-01-acme',
  url: '/?token=tok-abc',
}

const OPTIONS: SelectOption[] = [
  { value: 'mock-01-acme', label: 'Mock Exam 01 (17 tasks, 120m)' },
  { value: 'all', label: 'Full Curriculum (All 111 Tasks, Untimed)' },
]

async function tick(times = 2): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await nextTick()
    await flushPromises()
  }
}

beforeEach(() => {
  createSessionInviteMock.mockReset()
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('useAdminInvites — create (FE-033)', () => {
  it('POSTs the chosen preset and stores the returned invite', async () => {
    createSessionInviteMock.mockResolvedValueOnce(INVITE)
    const { createInvite, latestInvite, creating, error } = useAdminInvites()

    const result = await createInvite('mock-01-acme')

    expect(createSessionInviteMock).toHaveBeenCalledTimes(1)
    expect(createSessionInviteMock).toHaveBeenCalledWith('mock-01-acme')
    expect(result).toEqual(INVITE)
    expect(latestInvite.value).toEqual(INVITE)
    expect(error.value).toBeNull()
    expect(creating.value).toBe(false)
  })

  it('omits the preset when none is selected', async () => {
    createSessionInviteMock.mockResolvedValueOnce(INVITE)
    const { createInvite } = useAdminInvites()

    await createInvite()

    expect(createSessionInviteMock).toHaveBeenCalledWith(undefined)
  })

  it('surfaces a capacity-limit error and does not store an invite', async () => {
    createSessionInviteMock.mockRejectedValueOnce(
      new ApiError(429, 'Server resource limit reached — cannot start another session'),
    )
    const { createInvite, latestInvite, error, creating } = useAdminInvites()

    await expect(createInvite('mock-01-acme')).rejects.toThrow('Server resource limit reached')

    expect(error.value).toContain('Server resource limit reached')
    expect(latestInvite.value).toBeNull()
    expect(creating.value).toBe(false)
  })

  it('clears a previously stored invite when a later create fails', async () => {
    createSessionInviteMock.mockResolvedValueOnce(INVITE)
    createSessionInviteMock.mockRejectedValueOnce(new ApiError(429, 'Server resource limit reached'))
    const { createInvite, latestInvite } = useAdminInvites()

    await createInvite('mock-01-acme')
    expect(latestInvite.value).toEqual(INVITE)

    await expect(createInvite('mock-01-acme')).rejects.toThrow('Server resource limit reached')
    expect(latestInvite.value).toBeNull()
  })
})

describe('invite URL helpers (FE-033)', () => {
  it('composes an absolute URL from a root-relative invite path', () => {
    expect(buildInviteUrl('/?token=abc')).toBe(`${window.location.origin}/?token=abc`)
    expect(absoluteInviteUrl('/?token=abc', 'https://host')).toBe('https://host/?token=abc')
  })

  it('passes an already-absolute URL through unchanged', () => {
    const absolute = 'https://exam.example.com/?token=abc'
    expect(buildInviteUrl(absolute)).toBe(absolute)
    expect(absoluteInviteUrl(absolute, 'https://host')).toBe(absolute)
  })

  it('inserts a separator when the relative path lacks a leading slash', () => {
    expect(absoluteInviteUrl('?token=abc', 'https://host')).toBe('https://host/?token=abc')
  })
})

describe('copyTextToClipboard (FE-033)', () => {
  it('writes through the async Clipboard API when available', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    const ok = await copyTextToClipboard('https://host/?token=abc')

    expect(ok).toBe(true)
    expect(writeText).toHaveBeenCalledWith('https://host/?token=abc')
  })

  it('does nothing for empty text', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })

    expect(await copyTextToClipboard('')).toBe(false)
    expect(writeText).not.toHaveBeenCalled()
  })
})

describe('AdminInviteForm (FE-033)', () => {
  it('renders the preset options in the selector', async () => {
    const wrapper = mount(AdminInviteForm, { props: { options: OPTIONS } })
    await wrapper.get('[data-testid="invite-preset"]').trigger('click')
    await tick()

    const rendered = wrapper.findAll('[role="option"]').map((option) => option.text())
    expect(rendered).toEqual(OPTIONS.map((option) => option.label))
  })

  it('emits create with the selected preset', async () => {
    const wrapper = mount(AdminInviteForm, { props: { options: OPTIONS } })
    await wrapper.get('[data-testid="invite-preset"]').trigger('click')
    await tick()
    await wrapper.findAll('[role="option"]')[1].trigger('click')
    await tick()

    await wrapper.get('form').trigger('submit')

    expect(wrapper.emitted('create')?.[0]).toEqual(['all'])
  })

  it('hides the output box until an invite exists', () => {
    const wrapper = mount(AdminInviteForm, { props: { options: OPTIONS } })
    expect(wrapper.find('[data-testid="invite-output"]').exists()).toBe(false)
  })

  it('renders the copyable absolute URL and emits copy', async () => {
    const wrapper = mount(AdminInviteForm, { props: { options: OPTIONS, invite: INVITE } })
    const expected = `${window.location.origin}/?token=tok-abc`

    expect(wrapper.get('[data-testid="invite-output"]').text()).toContain('mock-01-acme')
    expect(wrapper.get('[data-testid="invite-url"]').text()).toBe(expected)

    await wrapper.get('[data-testid="invite-copy"]').trigger('click')
    expect(wrapper.emitted('copy')?.[0]).toEqual([expected])
  })

  it('emits start with the invite token', async () => {
    const wrapper = mount(AdminInviteForm, { props: { options: OPTIONS, invite: INVITE } })

    await wrapper.get('[data-testid="invite-start"]').trigger('click')

    expect(wrapper.emitted('start')?.[0]).toEqual([INVITE.token])
  })

  it('does not emit start while starting', async () => {
    const wrapper = mount(AdminInviteForm, {
      props: { options: OPTIONS, invite: INVITE, starting: true },
    })

    await wrapper.get('[data-testid="invite-start"]').trigger('click')

    expect(wrapper.emitted('start')).toBeUndefined()
  })
})
