import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { generatePreset } from '@/api/presets'
import type { GeneratePresetResponse } from '@/api/presets'
import { ApiError } from '@/api/client'
import PresetBuilder from '@/components/admin/PresetBuilder.vue'

/**
 * FS-007 — the admin "Custom exam" builder.
 *
 * Presentational behaviour only: the component collects count + optional
 * difficulty/domains, calls `generatePreset`, and never renders a question list.
 */

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  session: { apply: vi.fn() },
}))

vi.mock('@/api/presets', () => ({ generatePreset: vi.fn() }))
vi.mock('@/stores/session', () => ({ useSessionStore: () => mocks.session }))
vi.mock('@/composables/useToast', () => ({ useToast: () => ({ push: mocks.push }) }))

// Headless UI (Select) observes its panel with ResizeObserver and scrolls the
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

const generatePresetMock = vi.mocked(generatePreset)

const ACTIVE_SESSION = {
  active: true,
  session_id: 'sess-generated-1',
  name: 'Generated Exam (7 Questions)',
  mode: 'sequential',
  status: 'active',
  current_index: 0,
  total_tasks: 7,
  time_remaining_seconds: null,
  created_at: '2026-09-11T00:00:00Z',
  server_timestamp: 0,
  flagged_ids: [],
  is_admin: true,
} as unknown as GeneratePresetResponse

async function tick(times = 2): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await nextTick()
    await flushPromises()
  }
}

function mountBuilder() {
  return mount(PresetBuilder)
}

function countInput(wrapper: ReturnType<typeof mountBuilder>) {
  return wrapper.get('[data-testid="preset-builder-count"] input')
}

async function chooseDifficulty(
  wrapper: ReturnType<typeof mountBuilder>,
  label: string,
): Promise<void> {
  await wrapper.get('[data-testid="preset-builder-difficulty"]').trigger('click')
  await tick()
  const option = wrapper.findAll('[role="option"]').find((item) => item.text() === label)
  if (!option) throw new Error(`Difficulty option "${label}" not found`)
  await option.trigger('click')
  await tick()
}

beforeEach(() => {
  generatePresetMock.mockReset()
  mocks.push.mockReset()
  mocks.session.apply.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('PresetBuilder (FS-007)', () => {
  it('enforces the count limits client-side without calling the API', async () => {
    const wrapper = mountBuilder()
    await countInput(wrapper).setValue('51')
    await wrapper.get('form').trigger('submit')
    await tick()

    expect(generatePresetMock).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Count must be between 1 and 50.')
    expect(mocks.push).toHaveBeenCalledWith(
      expect.objectContaining({ variant: 'warning' }),
    )
    wrapper.unmount()
  })

  it('rejects non-integer counts', async () => {
    const wrapper = mountBuilder()
    await countInput(wrapper).setValue('2.5')
    await wrapper.get('form').trigger('submit')
    await tick()

    expect(generatePresetMock).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('passes count, difficulty and domains through to generatePreset', async () => {
    generatePresetMock.mockResolvedValueOnce(ACTIVE_SESSION)
    const wrapper = mountBuilder()

    await countInput(wrapper).setValue('12')
    await chooseDifficulty(wrapper, 'Hard')
    await wrapper.get('[data-testid="preset-builder-domain-storage"]').setValue(true)
    await wrapper.get('[data-testid="preset-builder-domain-security"]').setValue(true)
    await wrapper.get('form').trigger('submit')
    await tick()

    expect(generatePresetMock).toHaveBeenCalledTimes(1)
    expect(generatePresetMock).toHaveBeenCalledWith({
      count: 12,
      difficulty: 'hard',
      domains: ['storage', 'security'],
    })
    wrapper.unmount()
  })

  it('omits optional fields when left untouched', async () => {
    generatePresetMock.mockResolvedValueOnce(ACTIVE_SESSION)
    const wrapper = mountBuilder()

    await wrapper.get('form').trigger('submit')
    await tick()

    expect(generatePresetMock).toHaveBeenCalledWith({ count: 5 })
    wrapper.unmount()
  })

  it('shows a summary, applies the session and renders no questions on success', async () => {
    generatePresetMock.mockResolvedValueOnce(ACTIVE_SESSION)
    const wrapper = mountBuilder()

    await wrapper.get('form').trigger('submit')
    await tick()

    expect(wrapper.get('[data-testid="preset-builder-summary"]').text()).toBe(
      'Started session with 7 tasks',
    )
    expect(mocks.session.apply).toHaveBeenCalledWith(ACTIVE_SESSION)
    expect(mocks.push).toHaveBeenCalledWith(
      expect.objectContaining({ variant: 'success', message: 'Started session with 7 tasks' }),
    )
    // Acceptance: no individual questions are ever rendered.
    expect(wrapper.find('[data-testid*="question"]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('Generated Exam')
    wrapper.unmount()
  })

  it('surfaces a 429 error through a toast and shows no summary', async () => {
    generatePresetMock.mockRejectedValueOnce(
      new ApiError(429, 'Server resource limit reached — cannot start another session'),
    )
    const wrapper = mountBuilder()

    await wrapper.get('form').trigger('submit')
    await tick()

    expect(mocks.session.apply).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="preset-builder-summary"]').exists()).toBe(false)
    expect(mocks.push).toHaveBeenCalledWith(
      expect.objectContaining({
        variant: 'error',
        message: expect.stringContaining('Server resource limit reached'),
      }),
    )
    wrapper.unmount()
  })

  it('surfaces a 400 error through a toast', async () => {
    generatePresetMock.mockRejectedValueOnce(new ApiError(400, 'No questions match the filters'))
    const wrapper = mountBuilder()

    await wrapper.get('form').trigger('submit')
    await tick()

    expect(mocks.push).toHaveBeenCalledWith(
      expect.objectContaining({
        variant: 'error',
        message: expect.stringContaining('No questions match the filters'),
      }),
    )
    wrapper.unmount()
  })
})
