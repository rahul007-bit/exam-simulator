import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import TaskPane from '@/components/candidate/TaskPane.vue'
import type { TaskPaneTask } from '@/components/candidate/task'

/**
 * FE-022 navigation footer — legacy parity coverage for the left-pane footer bar
 * (`Previous` · `Reset task` · `Task X of Y` · `Next`). The footer mirrors the
 * legacy disabled rules: Previous at the first task, Next at the last task, and
 * every control while an action is in flight.
 */

const TASK: TaskPaneTask = {
  task_num: 1,
  title: 'Task One',
  description: 'Apply the manifest.',
  points: 1,
}

const MARKDOWN_STUB = {
  name: 'MarkdownRenderer',
  props: ['source', 'emptyText'],
  template: '<div data-testid="markdown-stub" />',
}

function mountPane(props: Record<string, unknown>) {
  return mount(TaskPane, {
    props: { task: TASK, taskNum: 2, totalTasks: 5, ...props },
    global: { stubs: { MarkdownRenderer: MARKDOWN_STUB } },
  })
}

describe('TaskPane navigation footer — FE-022', () => {
  it('renders the footer with the task progress text', () => {
    const wrapper = mountPane({ taskNum: 2, totalTasks: 5 })
    expect(wrapper.find('[data-testid="task-footer"]').exists()).toBe(true)
    expect(wrapper.get('[data-testid="task-progress-text"]').text()).toBe('Task 2 of 5')
    wrapper.unmount()
  })

  it('emits prev / next / reset when the controls are clicked', async () => {
    const wrapper = mountPane({ taskNum: 2, totalTasks: 5 })

    await wrapper.get('[data-testid="task-prev"]').trigger('click')
    await wrapper.get('[data-testid="task-next"]').trigger('click')
    await wrapper.get('[data-testid="task-reset"]').trigger('click')

    expect(wrapper.emitted('prev')).toHaveLength(1)
    expect(wrapper.emitted('next')).toHaveLength(1)
    expect(wrapper.emitted('reset')).toHaveLength(1)
    wrapper.unmount()
  })

  it('disables Previous on the first task and Next on the last task', () => {
    const first = mountPane({ taskNum: 1, totalTasks: 5 })
    expect(first.get('[data-testid="task-prev"]').attributes('disabled')).toBeDefined()
    expect(first.get('[data-testid="task-next"]').attributes('disabled')).toBeUndefined()
    first.unmount()

    const last = mountPane({ taskNum: 5, totalTasks: 5 })
    expect(last.get('[data-testid="task-prev"]').attributes('disabled')).toBeUndefined()
    expect(last.get('[data-testid="task-next"]').attributes('disabled')).toBeDefined()
    last.unmount()
  })

  it('disables the controls while an action is busy', () => {
    const wrapper = mountPane({ taskNum: 2, totalTasks: 5, busy: true })
    expect(wrapper.get('[data-testid="task-prev"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-testid="task-reset"]').attributes('disabled')).toBeDefined()
    expect(wrapper.get('[data-testid="task-next"]').attributes('disabled')).toBeDefined()
    wrapper.unmount()
  })

  it('omits the footer entirely when there is no task', () => {
    const wrapper = mountPane({ task: null })
    expect(wrapper.find('[data-testid="task-footer"]').exists()).toBe(false)
    wrapper.unmount()
  })
})
