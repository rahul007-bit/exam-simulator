import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { describe, expect, it, vi } from 'vitest'

import QuestionDrawer from '@/components/candidate/QuestionDrawer.vue'
import {
  navState,
  navStateLabel,
  navStateVariant,
  navSummary,
  type QuestionNavItem,
} from '@/components/candidate/question'

/**
 * FE-024 unit coverage for the question navigator state mapping and drawer.
 * The state machine mirrors the legacy drawer precedence
 * (current → flagged → scored → pending).
 */

// The UI `Modal` teleports to `<body>`; stub it so the drawer's own markup is
// queryable directly through the wrapper. Modal itself is covered by FE-012.
const MODAL_STUB = {
  name: 'Modal',
  props: ['modelValue', 'title', 'description', 'size'],
  template: '<div data-testid="modal-stub"><slot /><slot name="footer" /></div>',
}

async function tick(times = 2): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await nextTick()
    await flushPromises()
  }
}

const MOUNT_OPTIONS = { global: { stubs: { Modal: MODAL_STUB } } }

const ITEMS: QuestionNavItem[] = [
  {
    task_num: 1,
    id: 'q1',
    title: 'Current task',
    is_current: true,
    is_flagged: true,
    points: 5,
    target_context: 'k3d-cka',
  },
  { task_num: 2, id: 'q2', title: 'Flagged task', is_flagged: true, points: 4 },
  {
    task_num: 3,
    id: 'q3',
    title: 'Scored task',
    points: 3,
    score_data: { passed: true, score: 3, max_score: 3, message: 'ok' },
  },
  { task_num: 4, id: 'q4', title: 'Pending task', points: 2 },
]

describe('question navigator state mapping — FE-024', () => {
  it('applies legacy precedence: current > flagged > scored > pending', () => {
    expect(navState(ITEMS[0])).toBe('current')
    expect(navState(ITEMS[1])).toBe('flagged')
    expect(navState(ITEMS[2])).toBe('scored')
    expect(navState(ITEMS[3])).toBe('pending')
  })

  it('labels each state without emoji', () => {
    expect(navStateLabel('current')).toBe('Current')
    expect(navStateLabel('flagged')).toBe('Flagged')
    expect(navStateLabel('scored')).toBe('Scored')
    expect(navStateLabel('pending')).toBe('Pending')
  })

  it('maps states to semantic badge variants', () => {
    expect(navStateVariant('current')).toBe('accent')
    expect(navStateVariant('flagged')).toBe('warning')
    expect(navStateVariant('scored')).toBe('info')
    expect(navStateVariant('pending')).toBe('neutral')
  })

  it('summarises totals by effective state', () => {
    expect(navSummary(ITEMS)).toEqual({
      total: 4,
      current: 1,
      flagged: 1,
      scored: 1,
      pending: 1,
    })
  })
})

interface DrawerProps {
  modelValue: boolean
  questions?: QuestionNavItem[] | null
  loading?: boolean
  load?: (signal?: AbortSignal) => Promise<QuestionNavItem[]>
}

function mountDrawer(props: DrawerProps) {
  return mount(QuestionDrawer, { props, ...MOUNT_OPTIONS })
}

describe('QuestionDrawer — FE-024', () => {
  it('renders one item per task with its state', async () => {
    const wrapper = mountDrawer({ modelValue: true, questions: ITEMS })
    await tick()

    const items = wrapper.findAll('[data-testid="question-nav-item"]')
    expect(items).toHaveLength(4)

    // The card is a keyboard-operable div (it hosts a nested copy button).
    expect(items[0].element.tagName).toBe('DIV')
    expect(items[0].attributes('role')).toBe('button')
    expect(items[0].attributes('tabindex')).toBe('0')

    expect(items[0].attributes('data-state')).toBe('current')
    expect(items[0].attributes('aria-current')).toBe('true')
    expect(items[0].text()).toContain('Current')

    expect(items[1].attributes('data-state')).toBe('flagged')
    expect(items[1].text()).toContain('Flagged')

    expect(items[2].attributes('data-state')).toBe('scored')
    expect(items[2].text()).toContain('Scored')

    expect(items[3].attributes('data-state')).toBe('pending')
    expect(items[3].text()).toContain('Pending')

    wrapper.unmount()
  })

  it('shows the summary counts', async () => {
    const wrapper = mountDrawer({ modelValue: true, questions: ITEMS })
    await tick()
    expect(wrapper.get('[data-testid="question-nav-summary"]').text()).toContain('4 tasks')
    expect(wrapper.get('[data-testid="question-nav-summary"]').text()).toContain('1 flagged')
    wrapper.unmount()
  })

  it('emits select(task_num) and closes on click', async () => {
    const wrapper = mountDrawer({ modelValue: true, questions: ITEMS })
    await tick()

    await wrapper.findAll('[data-testid="question-nav-item"]')[1].trigger('click')
    await tick()

    expect(wrapper.emitted('select')?.[0]).toEqual([2])
    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([false])
    wrapper.unmount()
  })

  it('does not jump when the nested copy button handles Enter/Space', async () => {
    const wrapper = mountDrawer({ modelValue: true, questions: ITEMS })
    await tick()

    const card = wrapper.findAll('[data-testid="question-nav-item"]')[0]
    const copyButton = card.get('button')

    await copyButton.trigger('keydown.enter')
    await copyButton.trigger('keydown.space')
    await tick()

    expect(wrapper.emitted('select')).toBeUndefined()
    wrapper.unmount()
  })

  it('renders the empty state when there are no questions', async () => {
    const wrapper = mountDrawer({ modelValue: true, questions: [] })
    await tick()
    expect(wrapper.find('[data-testid="question-nav-grid"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('No questions available.')
    wrapper.unmount()
  })

  it('loads questions when uncontrolled and the modal opens', async () => {
    const loader = async (): Promise<QuestionNavItem[]> => ITEMS
    const wrapper = mountDrawer({ modelValue: true, load: loader })
    await tick()

    expect(wrapper.findAll('[data-testid="question-nav-item"]')).toHaveLength(4)
    wrapper.unmount()
  })

  it('re-loads questions on every open so the navigator reflects the current task', async () => {
    const loader = vi.fn(async (): Promise<QuestionNavItem[]> => ITEMS)
    const wrapper = mountDrawer({ modelValue: false, load: loader })
    await tick()
    expect(loader).not.toHaveBeenCalled()

    await wrapper.setProps({ modelValue: true })
    await tick()
    expect(loader).toHaveBeenCalledTimes(1)

    await wrapper.setProps({ modelValue: false })
    await tick()
    await wrapper.setProps({ modelValue: true })
    await tick()
    expect(loader).toHaveBeenCalledTimes(2)

    wrapper.unmount()
  })
})
