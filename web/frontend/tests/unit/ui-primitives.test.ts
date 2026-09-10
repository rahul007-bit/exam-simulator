import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import { describe, expect, it } from 'vitest'

import Badge from '@/components/ui/Badge.vue'
import Button from '@/components/ui/Button.vue'
import Card from '@/components/ui/Card.vue'
import Chip from '@/components/ui/Chip.vue'
import Input from '@/components/ui/Input.vue'
import Modal from '@/components/ui/Modal.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import Select from '@/components/ui/Select.vue'
import Spinner from '@/components/ui/Spinner.vue'
import type { SegmentOption, SelectOption } from '@/components/ui'

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

async function tick(times = 2): Promise<void> {
  for (let i = 0; i < times; i += 1) {
    await nextTick()
    await flushPromises()
  }
}

const OPTIONS: SelectOption[] = [
  { value: 'candidate', label: 'Candidate' },
  { value: 'admin', label: 'Administrator' },
  { value: 'reviewer', label: 'Reviewer', disabled: true },
]

const SEGMENTS: SegmentOption[] = [
  { value: 'desktop', label: 'Desktop' },
  { value: 'terminal', label: 'Terminal' },
  { value: 'replay', label: 'Replay', disabled: true },
]

describe('Button — FE-012', () => {
  it('renders its slot with a safe default type', () => {
    const wrapper = mount(Button, { slots: { default: 'Save' } })
    const button = wrapper.get('button')
    expect(button.text()).toBe('Save')
    expect(button.attributes('type')).toBe('button')
  })

  it('maps each variant to token utilities', () => {
    expect(mount(Button, { props: { variant: 'primary' } }).classes().join(' ')).toContain(
      'bg-accent-solid',
    )
    expect(mount(Button, { props: { variant: 'secondary' } }).classes().join(' ')).toContain(
      'border-border',
    )
    expect(mount(Button, { props: { variant: 'ghost' } }).classes().join(' ')).toContain(
      'bg-transparent',
    )
    expect(mount(Button, { props: { variant: 'danger' } }).classes().join(' ')).toContain(
      'text-danger-text',
    )
  })

  it('sizes use the fixed heights', () => {
    expect(mount(Button, { props: { size: 'sm' } }).classes().join(' ')).toContain('h-8')
    expect(mount(Button, { props: { size: 'lg' } }).classes().join(' ')).toContain('h-11')
  })

  it('applies the focus-ring tokens', () => {
    const classes = mount(Button).classes().join(' ')
    expect(classes).toContain('focus-visible:outline-2')
    expect(classes).toContain('focus-ring-color')
  })

  it('renders disabled state', () => {
    const wrapper = mount(Button, { props: { disabled: true } })
    expect(wrapper.get('button').attributes('disabled')).toBeDefined()
  })

  it('loading disables the button, sets aria-busy and shows a decorative spinner', () => {
    const wrapper = mount(Button, { props: { loading: true } })
    const button = wrapper.get('button')
    expect(button.attributes('disabled')).toBeDefined()
    expect(button.attributes('aria-busy')).toBe('true')
    expect(wrapper.find('svg.animate-spin').exists()).toBe(true)
    // The spinner inside a button is presentational (aria-busy announces it).
    expect(wrapper.find('[role="status"]').exists()).toBe(false)
  })
})

describe('Input — FE-012', () => {
  it('associates the label with the input', () => {
    const wrapper = mount(Input, { props: { label: 'Email', modelValue: 'a@b.co' } })
    const id = wrapper.get('input').attributes('id')
    expect(id).toBeTruthy()
    expect(wrapper.get('label').attributes('for')).toBe(id)
    expect((wrapper.get('input').element as HTMLInputElement).value).toBe('a@b.co')
  })

  it('emits update:modelValue on input', async () => {
    const wrapper = mount(Input, { props: { modelValue: '' } })
    await wrapper.get('input').setValue('hello')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['hello'])
  })

  it('wires error state to aria-invalid + aria-describedby', () => {
    const wrapper = mount(Input, {
      props: { label: 'Email', modelValue: 'x', error: 'Invalid email' },
    })
    const input = wrapper.get('input')
    expect(input.attributes('aria-invalid')).toBe('true')
    const describedBy = input.attributes('aria-describedby')
    expect(describedBy).toBeTruthy()
    expect(wrapper.find(`#${describedBy}`).text()).toBe('Invalid email')
  })

  it('exposes required semantics', () => {
    const wrapper = mount(Input, { props: { label: 'Name', required: true } })
    expect(wrapper.get('input').attributes('required')).toBeDefined()
    expect(wrapper.find('.sr-only').text()).toContain('required')
  })

  it('renders disabled and readonly states', () => {
    const wrapper = mount(Input, { props: { disabled: true, readonly: true } })
    const input = wrapper.get('input')
    expect(input.attributes('disabled')).toBeDefined()
    expect(input.attributes('readonly')).toBeDefined()
  })
})

describe('Select (Headless UI Listbox) — FE-012', () => {
  it('shows the placeholder until a value is chosen', () => {
    const wrapper = mount(Select, { props: { label: 'Role', options: OPTIONS } })
    expect(wrapper.get('button').text()).toContain('Select an option')
  })

  it('opens and emits the selected value', async () => {
    const wrapper = mount(Select, { props: { modelValue: '', options: OPTIONS } })
    await wrapper.get('button').trigger('click')
    await tick()

    const options = wrapper.findAll('[role="option"]')
    expect(options).toHaveLength(3)
    await options[1].trigger('click')
    await tick()

    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['admin'])
  })

  it('labels the control and disables options', async () => {
    const wrapper = mount(Select, { props: { label: 'Role', options: OPTIONS } })
    const labelId = wrapper.get('label').attributes('id')
    expect(labelId).toBeTruthy()
    await wrapper.get('button').trigger('click')
    await tick()
    expect(wrapper.get('[role="option"][aria-disabled="true"]').text()).toContain('Reviewer')
  })
})

describe('Badge & Chip — FE-012', () => {
  it('maps badge variants to semantic token families', () => {
    for (const [variant, token] of [
      ['success', 'text-success-text'],
      ['warning', 'text-warning-text'],
      ['danger', 'text-danger-text'],
      ['info', 'text-info-text'],
      ['accent', 'text-accent-text'],
    ] as const) {
      expect(mount(Badge, { props: { variant } }).classes().join(' ')).toContain(token)
    }
  })

  it('renders a removable chip with a labelled remove button that emits', async () => {
    const wrapper = mount(Chip, {
      props: { removable: true, removeLabel: 'Remove react' },
      slots: { default: 'react' },
    })
    const button = wrapper.get('button')
    expect(button.attributes('aria-label')).toBe('Remove react')
    await button.trigger('click')
    expect(wrapper.emitted('remove')).toHaveLength(1)
  })

  it('omits the remove button when not removable', () => {
    const wrapper = mount(Chip, { slots: { default: 'static' } })
    expect(wrapper.find('button').exists()).toBe(false)
  })
})

describe('Card — FE-012', () => {
  it('renders title, subtitle, body and footer slots', () => {
    const wrapper = mount(Card, {
      props: { title: 'Title', subtitle: 'Subtitle' },
      slots: { default: '<p>body</p>', footer: 'footer' },
    })
    expect(wrapper.get('h3').text()).toBe('Title')
    expect(wrapper.text()).toContain('Subtitle')
    expect(wrapper.text()).toContain('body')
    expect(wrapper.text()).toContain('footer')
  })

  it('maps variants to token classes', () => {
    expect(mount(Card, { props: { variant: 'elevated' } }).classes().join(' ')).toContain(
      'shadow-[var(--shadow-sm)]',
    )
    expect(mount(Card, { props: { variant: 'outlined' } }).classes().join(' ')).toContain(
      'border-border-strong',
    )
  })
})

describe('Modal (Headless UI Dialog) — FE-012', () => {
  async function mountOpen(): Promise<VueWrapper> {
    const wrapper = mount(Modal, {
      attachTo: document.body,
      props: { modelValue: true, title: 'Confirm', description: 'Are you sure?' },
      slots: { default: '<button type="button">content</button>' },
    })
    await tick(4)
    return wrapper
  }

  it('does not render when closed', () => {
    mount(Modal, { attachTo: document.body, props: { modelValue: false, title: 'Hidden' } })
    expect(document.body.querySelector('[data-testid="modal"]')).toBeNull()
  })

  it('renders an accessible, labelled dialog when open', async () => {
    const wrapper = await mountOpen()
    const dialog = document.body.querySelector('[data-testid="modal"]')
    expect(dialog).toBeTruthy()
    expect(dialog?.getAttribute('role')).toBe('dialog')
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    const labelledby = dialog?.getAttribute('aria-labelledby')
    expect(labelledby).toBeTruthy()
    expect(document.getElementById(labelledby as string)?.textContent).toContain('Confirm')
    wrapper.unmount()
  })

  it('emits update:modelValue=false on Escape', async () => {
    const wrapper = await mountOpen()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await tick(3)
    expect(wrapper.emitted('update:modelValue')?.at(-1)).toEqual([false])
    wrapper.unmount()
  })
})

describe('Spinner & SegmentedControl — FE-012', () => {
  it('announces a labelled spinner and hides a decorative one', () => {
    const announced = mount(Spinner, { props: { label: 'Loading data' } })
    expect(announced.get('[role="status"]').text()).toContain('Loading data')
    expect(announced.find('.sr-only').text()).toBe('Loading data')

    const decorative = mount(Spinner, { props: { decorative: true } })
    expect(decorative.find('[role="status"]').exists()).toBe(false)
    expect(decorative.get('svg').attributes('aria-hidden')).toBe('true')
  })

  it('renders a labelled radiogroup with roving checked state', () => {
    const wrapper = mount(SegmentedControl, {
      props: { modelValue: 'desktop', label: 'View', options: SEGMENTS },
    })
    expect(wrapper.get('[role="radiogroup"]')).toBeTruthy()
    const radios = wrapper.findAll('[role="radio"]')
    expect(radios).toHaveLength(3)
    expect(radios[0].attributes('aria-checked')).toBe('true')
    expect(radios[0].classes().join(' ')).toContain('bg-accent-solid')
    expect(radios[2].attributes('aria-disabled')).toBe('true')
  })

  it('emits the selected segment', async () => {
    const wrapper = mount(SegmentedControl, {
      props: { modelValue: 'desktop', options: SEGMENTS },
    })
    await wrapper.findAll('[role="radio"]')[1].trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual(['terminal'])
  })
})

describe('FE-012 constraints audit (hex / glow / emoji)', () => {
  const HEX = /#[0-9a-fA-F]{3,6}\b/
  const GLOW = /text-shadow|drop-shadow|blur\(/
  const EMOJI = /\p{Extended_Pictographic}/u

  function walk(dir: string): string[] {
    return readdirSync(dir).flatMap((entry) => {
      const full = join(dir, entry)
      return statSync(full).isDirectory() ? walk(full) : [full]
    })
  }

  const files = [
    ...walk(join(process.cwd(), 'src/components/ui')),
    join(process.cwd(), 'src/views/DevUiView.vue'),
  ].filter((file) => /\.(vue|ts)$/.test(file))

  it('has no raw hex colours in the primitives or gallery', () => {
    const offenders: string[] = []
    for (const file of files) {
      readFileSync(file, 'utf8')
        .split('\n')
        .forEach((line, index) => {
          if (HEX.test(line)) offenders.push(`${file}:${index + 1}`)
        })
    }
    expect(offenders).toEqual([])
  })

  it('has no glow/gradient primitives and no emoji in UI copy', () => {
    for (const file of files) {
      const text = readFileSync(file, 'utf8')
      expect(text, file).not.toMatch(GLOW)
      expect(text, file).not.toMatch(EMOJI)
    }
  })
})
