import { mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { taskBadges } from '@/components/candidate/task'
import Badge from '@/components/ui/Badge.vue'

/**
 * Opt-in copy behaviour for the shared `Badge` (candidate exam chips).
 *
 * The badge stays a plain `<span>` unless `copyable` is set, at which point it
 * becomes a labelled `<button>` that copies its text and flashes a `check`
 * icon. A neutral copyable badge renders with the accent treatment so
 * otherwise-plain chips read as interactive.
 */

let writeText: ReturnType<typeof vi.fn>
let parentClicks = 0
let parentKeydowns = 0

// A single parent definition reused by the propagation tests: it listens for
// both click and keydown so we can prove the nested copy button stops each.
const Parent = defineComponent({
  render: () =>
    h(
      'div',
      {
        onClick: () => {
          parentClicks += 1
        },
        onKeydown: () => {
          parentKeydowns += 1
        },
      },
      [h(Badge, { copyable: true, copyText: 'copy me' }, { default: () => 'copy me' })],
    ),
})

beforeEach(() => {
  writeText = vi.fn().mockResolvedValue(undefined)
  parentClicks = 0
  parentKeydowns = 0
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText },
  })
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.useRealTimers()
})

async function flushMicrotasks(times = 4): Promise<void> {
  for (let i = 0; i < times; i += 1) await Promise.resolve()
  await nextTick()
}

describe('Badge copy support', () => {
  it('renders a plain span (no interactive control) by default', () => {
    const wrapper = mount(Badge, { slots: { default: 'Task 1' } })
    expect(wrapper.element.tagName).toBe('SPAN')
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('renders an interactive button when copyable', () => {
    const wrapper = mount(Badge, { props: { copyable: true }, slots: { default: 'Task 1' } })
    const button = wrapper.get('button')
    expect(button.attributes('type')).toBe('button')
    expect(button.text()).toContain('Task 1')
  })

  it('copies the provided text and emits copy on click', async () => {
    const wrapper = mount(Badge, {
      props: { copyable: true, copyText: 'context: k3d-cka' },
      slots: { default: 'context: k3d-cka' },
    })

    await wrapper.get('button').trigger('click')
    await flushMicrotasks()

    expect(writeText).toHaveBeenCalledWith('context: k3d-cka')
    expect(wrapper.emitted('copy')?.[0]).toEqual(['context: k3d-cka'])
  })

  it('falls back to the slot text when copyText is omitted', async () => {
    const wrapper = mount(Badge, { props: { copyable: true }, slots: { default: '5 pts' } })

    await wrapper.get('button').trigger('click')
    await flushMicrotasks()

    expect(writeText).toHaveBeenCalledWith('5 pts')
  })

  it('stops propagation so a nested badge does not activate its parent', async () => {
    const wrapper = mount(Parent)
    await wrapper.get('button').trigger('click')
    await flushMicrotasks()
    expect(parentClicks).toBe(0)

    // Sanity check: the parent listener itself is live.
    await wrapper.get('div').trigger('click')
    expect(parentClicks).toBe(1)
  })

  it('stops keydown propagation so Enter/Space do not activate a parent card', async () => {
    const wrapper = mount(Parent)
    const button = wrapper.get('button')

    const enter = new KeyboardEvent('keydown', {
      key: 'Enter',
      bubbles: true,
      cancelable: true,
    })
    button.element.dispatchEvent(enter)
    await flushMicrotasks()

    // The parent card never sees the event…
    expect(parentKeydowns).toBe(0)
    // …and `.stop` must not cancel the default action, so the button's own
    // native activation (which fires `click`) is preserved.
    expect(enter.defaultPrevented).toBe(false)

    await button.trigger('keydown.space')
    await flushMicrotasks()
    expect(parentKeydowns).toBe(0)

    // Keyboard activation ends in a click; copying still works.
    await button.trigger('click')
    await flushMicrotasks()
    expect(writeText).toHaveBeenCalledWith('copy me')

    // Sanity check: the parent listener itself is live.
    await wrapper.get('div').trigger('keydown.enter')
    expect(parentKeydowns).toBe(1)
  })

  it('flashes a copied state and reverts after ~1.2s', async () => {
    vi.useFakeTimers()
    const wrapper = mount(Badge, {
      props: { copyable: true, copyText: 'FLAGGED' },
      slots: { default: 'FLAGGED' },
    })

    // Copy icon draws two paths; the check icon draws one.
    expect(wrapper.findAll('path')).toHaveLength(2)

    await wrapper.get('button').trigger('click')
    await flushMicrotasks()
    expect(wrapper.findAll('path')).toHaveLength(1)

    vi.advanceTimersByTime(1200)
    await nextTick()
    expect(wrapper.findAll('path')).toHaveLength(2)
  })

  it('renders a neutral copyable badge with accent styling', () => {
    const accent = mount(Badge, { props: { copyable: true }, slots: { default: 'ns: default' } })
    expect(accent.classes().join(' ')).toContain('text-accent-text')

    const neutral = mount(Badge, { slots: { default: 'ns: default' } })
    expect(neutral.classes().join(' ')).toContain('text-text-muted')
  })

  it('keeps semantic variants and derives an accessible name', () => {
    const wrapper = mount(Badge, {
      props: { copyable: true, variant: 'warning', copyText: '2 flagged' },
      slots: { default: '2 flagged' },
    })
    expect(wrapper.classes().join(' ')).toContain('text-warning-text')
    expect(wrapper.get('button').attributes('aria-label')).toBe('Copy "2 flagged"')

    const custom = mount(Badge, {
      props: { copyable: true, copyText: 'x', copyLabel: 'Copy the flag count' },
      slots: { default: 'x' },
    })
    expect(custom.get('button').attributes('aria-label')).toBe('Copy the flag count')
  })
})

describe('taskBadges copy text', () => {
  const task = {
    task_num: 3,
    title: 'Scale a deployment',
    description: 'body',
    points: 5,
    namespace: 'batch-processing',
    target_context: 'k3d-prod',
  }

  it('copies the raw context/namespace value while keeping the descriptive label', () => {
    const badges = taskBadges(task)
    const context = badges.find((badge) => badge.key === 'context')
    const namespace = badges.find((badge) => badge.key === 'namespace')

    expect(context?.label).toBe('context: k3d-prod')
    expect(context?.copy).toBe('k3d-prod')
    expect(namespace?.label).toBe('ns: batch-processing')
    expect(namespace?.copy).toBe('batch-processing')
  })

  it('falls back to defaults and leaves non-metadata badges without a copy override', () => {
    const badges = taskBadges({ ...task, target_context: null, namespace: null })
    expect(badges.find((badge) => badge.key === 'context')?.copy).toBe('k3d-cka')
    expect(badges.find((badge) => badge.key === 'namespace')?.copy).toBe('default')
    expect(badges.find((badge) => badge.key === 'number')?.copy).toBeUndefined()
    expect(badges.find((badge) => badge.key === 'points')?.copy).toBeUndefined()
  })
})
