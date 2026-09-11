import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h, nextTick, ref } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import ReplayPlayer from '@/components/workspace/ReplayPlayer.vue'

import type { RecordingEvent } from '@/api/recordings'

/**
 * FE-029 replay island: the player owns the actor/channel selector (User ▾
 * Web/Desktop + Admin), fetches the selected channel's cast itself, swaps
 * channels without resetting the timeline, and filters the event timeline by
 * the active channel (legacy events with no `channel` belong to `user-web`).
 *
 * xterm.js is mocked because its module init touches canvas/layout APIs jsdom
 * does not implement; the replay engine only needs `reset`/`write`.
 */

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

const mocks = vi.hoisted(() => ({ getRecordingCast: vi.fn() }))

vi.mock('@/api/recordings', () => ({ getRecordingCast: mocks.getRecordingCast }))

if (!('ResizeObserver' in globalThis)) {
  class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver = ResizeObserverStub
}

const CAST = [
  '{"version":2,"width":80,"height":24,"duration":30}',
  '[0, "o", "boot"]',
  '[10, "o", "hello"]',
  '[20, "o", "world"]',
].join('\n')

const EVENTS: RecordingEvent[] = [
  { event: 'SESSION_START', rel_time: 0, channel: 'user-web', data: { name: 'Mock Exam' } },
  { event: 'DESKTOP_TERMINAL_INPUT', rel_time: 5, channel: 'user-desktop', data: { text: 'ls' } },
  { event: 'ADMIN_ACTION', rel_time: 10, channel: 'admin-web', data: { action: 'observe' } },
  {
    event: 'TASK_DEPLOYED',
    rel_time: 15,
    data: { task_num: 1, question_id: 'q1', title: 'Legacy' },
  },
]

async function tick(times = 3): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await nextTick()
    await flushPromises()
  }
}

type ExposedReplay = { seek: (seconds: number) => void }

/**
 * A tiny controlled host so a menu click round-trips through `update:channel`
 * exactly like `RecordingsModal` does in production.
 */
function mountHarness(options: { hasCast?: boolean } = {}) {
  const Harness = defineComponent({
    name: 'ReplayPlayerHarness',
    setup() {
      const channel = ref('user-web')
      return () =>
        h(ReplayPlayer, {
          sessionId: 'sess-1',
          channel: channel.value,
          hasCast: options.hasCast ?? true,
          events: EVENTS,
          'onUpdate:channel': (value: string) => {
            channel.value = value
          },
        })
    },
  })
  return mount(Harness)
}

beforeEach(() => {
  mocks.getRecordingCast.mockReset()
  mocks.getRecordingCast.mockResolvedValue(CAST)
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('ReplayPlayer — actor/channel controls', () => {
  it('renders the actor selector and the Events/Tasks tabs in one header row', async () => {
    const wrapper = mountHarness()
    await tick()

    const controls = wrapper.get('[data-testid="replay-controls"]')
    expect(controls.find('[data-testid="recording-tab-user"]').exists()).toBe(true)
    expect(controls.find('[data-testid="recording-tab-admin"]').exists()).toBe(true)
    expect(controls.find('[aria-label="Replay timeline"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('always offers Web and Desktop in the User menu', async () => {
    const wrapper = mountHarness({ hasCast: false })
    await tick()

    await wrapper.get('[data-testid="recording-tab-user"]').trigger('click')
    await tick()

    const items = wrapper.findAll('[role="menuitem"]')
    expect(items).toHaveLength(2)
    expect(items[0].text()).toContain('Web')
    expect(items[1].text()).toContain('Desktop')

    wrapper.unmount()
  })

  it('selects Desktop through the User menu and updates the channel', async () => {
    const wrapper = mountHarness()
    await tick()

    expect(wrapper.findComponent(ReplayPlayer).props('channel')).toBe('user-web')

    await wrapper.get('[data-testid="recording-tab-user"]').trigger('click')
    await tick()
    await wrapper.findAll('[role="menuitem"]')[1].trigger('click')
    await tick()

    expect(wrapper.findComponent(ReplayPlayer).props('channel')).toBe('user-desktop')
    expect(mocks.getRecordingCast.mock.calls.at(-1)?.[1]).toBe('user-desktop')

    wrapper.unmount()
  })

  it('selects the Admin tab and updates the channel', async () => {
    const wrapper = mountHarness()
    await tick()

    await wrapper.get('[data-testid="recording-tab-admin"]').trigger('click')
    await tick()

    expect(wrapper.findComponent(ReplayPlayer).props('channel')).toBe('admin-web')
    expect(wrapper.get('[data-testid="recording-tab-admin"]').attributes('aria-selected')).toBe(
      'true',
    )

    wrapper.unmount()
  })
})

describe('ReplayPlayer — event filtering by channel', () => {
  it('shows web events (and legacy no-channel events) for user-web', async () => {
    const wrapper = mountHarness()
    await tick()

    const events = wrapper.findAll('[data-testid="replay-event"]')
    expect(events).toHaveLength(2)
    expect(events.map((event) => event.text()).join(' ')).toContain('Legacy')

    wrapper.unmount()
  })

  it('shows only desktop events for user-desktop', async () => {
    const wrapper = mountHarness()
    await tick()

    await wrapper.get('[data-testid="recording-tab-user"]').trigger('click')
    await tick()
    await wrapper.findAll('[role="menuitem"]')[1].trigger('click')
    await tick()

    const events = wrapper.findAll('[data-testid="replay-event"]')
    expect(events).toHaveLength(1)
    expect(events[0].text()).toContain('DESKTOP_TERMINAL_INPUT')

    wrapper.unmount()
  })

  it('shows only admin events for admin-web', async () => {
    const wrapper = mountHarness()
    await tick()

    await wrapper.get('[data-testid="recording-tab-admin"]').trigger('click')
    await tick()

    const events = wrapper.findAll('[data-testid="replay-event"]')
    expect(events).toHaveLength(1)
    expect(events[0].text()).toContain('ADMIN_ACTION')

    wrapper.unmount()
  })
})

describe('ReplayPlayer — channel switching', () => {
  it('loads the active channel cast through the API', async () => {
    const wrapper = mount(ReplayPlayer, {
      props: { sessionId: 'sess-1', channel: 'user-web' },
    })
    await tick()

    expect(mocks.getRecordingCast).toHaveBeenCalledTimes(1)
    expect(mocks.getRecordingCast.mock.calls[0][0]).toBe('sess-1')
    expect(mocks.getRecordingCast.mock.calls[0][1]).toBe('user-web')

    wrapper.unmount()
  })

  it('preserves the playhead when the channel changes', async () => {
    const wrapper = mount(ReplayPlayer, {
      props: { sessionId: 'sess-1', channel: 'user-web' },
    })
    await tick()

    ;(wrapper.vm as unknown as ExposedReplay).seek(15)
    await tick()
    expect(wrapper.get('[data-testid="replay-time"]').text()).toContain('00:15')

    await wrapper.setProps({ channel: 'user-desktop' })
    await tick()

    expect(mocks.getRecordingCast.mock.calls.at(-1)?.[1]).toBe('user-desktop')
    expect(wrapper.get('[data-testid="replay-time"]').text()).toContain('00:15')

    wrapper.unmount()
  })

  it('shows the loading state until the cast resolves', async () => {
    let resolveCast: (value: string) => void = () => {}
    mocks.getRecordingCast.mockReturnValue(
      new Promise<string>((resolve) => {
        resolveCast = resolve
      }),
    )

    const wrapper = mount(ReplayPlayer, {
      props: { sessionId: 'sess-1', channel: 'user-web' },
    })
    await tick()

    expect(wrapper.find('[data-testid="replay-loading"]').exists()).toBe(true)

    resolveCast(CAST)
    await tick()
    expect(wrapper.find('[data-testid="replay-loading"]').exists()).toBe(false)

    wrapper.unmount()
  })

  it('keeps the timeline working when the channel has no cast', async () => {
    const wrapper = mount(ReplayPlayer, {
      props: { sessionId: 'sess-1', channel: 'user-desktop', hasCast: false, events: EVENTS },
    })
    await tick()

    expect(wrapper.get('[data-testid="recording-no-cast"]').text()).toContain(
      'No recording for this terminal',
    )
    expect(mocks.getRecordingCast).not.toHaveBeenCalled()
    expect(wrapper.findAll('[data-testid="replay-event"]')).toHaveLength(1)

    wrapper.unmount()
  })
})
