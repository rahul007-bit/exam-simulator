import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { RecordingDetail, RecordingEvent } from '@/api/recordings'

/**
 * FE-029 per-channel recordings: the modal owns the selected channel and the
 * `ReplayPlayer` renders the actor/channel selector (User ▾ Web/Desktop +
 * Admin) aligned with the Events/Tasks tabs, filters the timeline by channel,
 * and shows a graceful empty terminal when a channel has no cast.
 */

const apiMocks = vi.hoisted(() => ({
  getRecordingCast: vi.fn(),
  getRecording: vi.fn(),
  listRecordings: vi.fn(),
  recordingCastUrl: vi.fn(
    (sessionId: string, channel?: string) =>
      `/api/recordings/${sessionId}/cast${channel ? `?channel=${channel}` : ''}`,
  ),
  recordingEventsUrl: vi.fn((sessionId: string) => `/api/recordings/${sessionId}/events`),
}))

vi.mock('@/api/recordings', () => apiMocks)

// ReplayPlayer pulls in xterm.js, whose module init touches canvas/layout APIs
// jsdom does not implement; the replay engine only needs `reset`/`write`.
vi.mock('@xterm/xterm', () => ({
  Terminal: class {
    open(): void {}
    loadAddon(): void {}
    dispose(): void {}
    reset(): void {}
    write(): void {}
  },
}))

vi.mock('@xterm/addon-fit', () => ({
  FitAddon: class {
    fit(): void {}
  },
}))

import RecordingsModal from '@/components/candidate/RecordingsModal.vue'
import ReplayPlayer from '@/components/workspace/ReplayPlayer.vue'

const CAST = ['{"version":2,"width":80,"height":24,"duration":30}', '[0, "o", "boot"]'].join('\n')

const ModalStub = defineComponent({
  name: 'ModalStub',
  props: { modelValue: { type: Boolean, default: false } },
  emits: ['update:modelValue'],
  setup(_props, { slots }) {
    return () => h('div', { 'data-testid': 'modal' }, [slots.default?.(), slots.footer?.()])
  },
})

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

const EVENTS: RecordingEvent[] = [
  { event: 'SESSION_START', rel_time: 0, channel: 'user-web', data: { name: 'Mock Exam' } },
  { event: 'DESKTOP_TERMINAL_INPUT', rel_time: 5, channel: 'user-desktop', data: { text: 'ls' } },
  { event: 'ADMIN_ACTION', rel_time: 8, channel: 'admin-web', data: { action: 'observe' } },
  {
    event: 'TASK_DEPLOYED',
    rel_time: 12,
    data: { task_num: 1, question_id: 'q1', title: 'Legacy' },
  },
]

const ALL_CHANNELS: RecordingDetail = {
  session_id: 'sess-1',
  name: 'Mock Exam',
  events: EVENTS,
  events_count: EVENTS.length,
  task_timeline: [],
  has_cast: true,
  cast_size_bytes: 100,
  duration_seconds: 120,
  channels: [
    { id: 'user-web', has_cast: true, cast_size_bytes: 100 },
    { id: 'user-desktop', has_cast: true, cast_size_bytes: 100 },
    { id: 'admin-web', has_cast: true, cast_size_bytes: 100 },
  ],
}

async function tick(times = 4): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await nextTick()
    await flushPromises()
  }
}

async function mountOpen(detail: RecordingDetail) {
  apiMocks.getRecording.mockResolvedValue(detail)
  const wrapper = mount(RecordingsModal, {
    props: { modelValue: false, initialSessionId: 'sess-1', showList: false },
    global: { stubs: { Modal: ModalStub } },
  })
  await wrapper.setProps({ modelValue: true })
  await tick()
  return wrapper
}

async function openUserMenu(wrapper: Awaited<ReturnType<typeof mountOpen>>) {
  await wrapper.get('[data-testid="recording-tab-user"]').trigger('click')
  await tick()
}

beforeEach(() => {
  vi.clearAllMocks()
  apiMocks.listRecordings.mockResolvedValue({ recordings: [], total: 0 })
  apiMocks.getRecordingCast.mockResolvedValue(CAST)
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('RecordingsModal — channel tabs and dropdown', () => {
  it('renders the actor selector and Events/Tasks in the same header row', async () => {
    const wrapper = await mountOpen(ALL_CHANNELS)

    const controls = wrapper.get('[data-testid="replay-controls"]')
    expect(controls.find('[data-testid="recording-tab-user"]').exists()).toBe(true)
    expect(controls.find('[data-testid="recording-tab-admin"]').exists()).toBe(true)
    expect(controls.find('[aria-label="Replay timeline"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('does not render a separate floating channel select', async () => {
    const wrapper = await mountOpen(ALL_CHANNELS)

    expect(wrapper.find('[data-testid="recording-channel-select"]').exists()).toBe(false)

    wrapper.unmount()
  })

  it('selects the Desktop stream and passes user-desktop to ReplayPlayer', async () => {
    const wrapper = await mountOpen(ALL_CHANNELS)

    expect(wrapper.findComponent(ReplayPlayer).props('channel')).toBe('user-web')

    await openUserMenu(wrapper)
    const options = wrapper.findAll('[role="menuitem"]')
    expect(options).toHaveLength(2)
    expect(options[0].text()).toContain('Web')
    expect(options[1].text()).toContain('Desktop')

    await options[1].trigger('click')
    await tick()

    expect(wrapper.findComponent(ReplayPlayer).props('channel')).toBe('user-desktop')
    expect(wrapper.findComponent(ReplayPlayer).props('sessionId')).toBe('sess-1')
    expect(apiMocks.getRecordingCast.mock.calls.at(-1)?.[1]).toBe('user-desktop')

    wrapper.unmount()
  })

  it('filters the event timeline to the selected channel', async () => {
    const wrapper = await mountOpen(ALL_CHANNELS)
    expect(wrapper.findAll('[data-testid="replay-event"]')).toHaveLength(2)

    await openUserMenu(wrapper)
    await wrapper.findAll('[role="menuitem"]')[1].trigger('click')
    await tick()
    let events = wrapper.findAll('[data-testid="replay-event"]')
    expect(events).toHaveLength(1)
    expect(events[0].text()).toContain('DESKTOP_TERMINAL_INPUT')

    await wrapper.get('[data-testid="recording-tab-admin"]').trigger('click')
    await tick()
    events = wrapper.findAll('[data-testid="replay-event"]')
    expect(events).toHaveLength(1)
    expect(events[0].text()).toContain('ADMIN_ACTION')

    wrapper.unmount()
  })

  it('switches to the Admin tab and exposes proper tab semantics', async () => {
    const wrapper = await mountOpen(ALL_CHANNELS)

    const tablist = wrapper.get('[role="tablist"]')
    expect(tablist.attributes('aria-label')).toBe('Recording channels')

    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs).toHaveLength(2)
    expect(tabs[0].text()).toBe('User')
    expect(tabs[1].text()).toBe('Admin')
    expect(tabs[0].attributes('aria-selected')).toBe('true')
    expect(tabs[0].attributes('aria-controls')).toBeTruthy()

    await tabs[1].trigger('click')
    await tick()

    expect(tabs[1].attributes('aria-selected')).toBe('true')
    expect(wrapper.find('[role="tabpanel"]').exists()).toBe(true)
    expect(wrapper.findComponent(ReplayPlayer).props('channel')).toBe('admin-web')

    wrapper.unmount()
  })

  it('keeps the event list working when the selected channel has no cast', async () => {
    const detail: RecordingDetail = {
      ...ALL_CHANNELS,
      channels: [
        { id: 'user-web', has_cast: true, cast_size_bytes: 100 },
        { id: 'user-desktop', has_cast: false, cast_size_bytes: 0 },
        { id: 'admin-web', has_cast: true, cast_size_bytes: 100 },
      ],
    }
    const wrapper = await mountOpen(detail)

    await openUserMenu(wrapper)
    await wrapper.findAll('[role="menuitem"]')[1].trigger('click')
    await tick()

    expect(wrapper.get('[data-testid="recording-no-cast"]').text()).toContain(
      'No recording for this terminal',
    )
    expect(wrapper.findComponent(ReplayPlayer).props('hasCast')).toBe(false)
    const events = wrapper.findAll('[data-testid="replay-event"]')
    expect(events).toHaveLength(1)
    expect(events[0].text()).toContain('DESKTOP_TERMINAL_INPUT')

    wrapper.unmount()
  })

  it('always offers Web and Desktop for a legacy single-channel recording', async () => {
    const detail: RecordingDetail = { ...ALL_CHANNELS, channels: undefined }
    const wrapper = await mountOpen(detail)

    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs).toHaveLength(2)
    expect(tabs[0].text()).toBe('User')
    expect(tabs[1].text()).toBe('Admin')

    await openUserMenu(wrapper)
    expect(wrapper.findAll('[role="menuitem"]')).toHaveLength(2)

    wrapper.unmount()
  })

  it('always offers both user streams when only a user channel is exposed', async () => {
    const detail: RecordingDetail = {
      ...ALL_CHANNELS,
      channels: [{ id: 'user-web', has_cast: true, cast_size_bytes: 100 }],
    }
    const wrapper = await mountOpen(detail)

    const tabs = wrapper.findAll('[role="tab"]')
    expect(tabs).toHaveLength(2)

    await openUserMenu(wrapper)
    expect(wrapper.findAll('[role="menuitem"]')).toHaveLength(2)

    wrapper.unmount()
  })
})
