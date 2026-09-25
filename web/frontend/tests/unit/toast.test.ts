import { readFileSync } from 'node:fs'
import { join } from 'node:path'

import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import Toaster from '@/components/Toaster.vue'
import { DEFAULT_TOAST_DURATION, useToast } from '@/composables/useToast'
import type { ToastVariant } from '@/composables/useToast'

const { push, dismiss, clear, toasts } = useToast()

const VARIANTS: ToastVariant[] = ['info', 'success', 'warning', 'error']

describe('useToast + Toaster — FE-010 T1', () => {
  beforeEach(() => {
    clear()
    vi.useFakeTimers()
  })

  afterEach(() => {
    clear()
    vi.useRealTimers()
  })

  it('exposes the documented push/dismiss/clear API', () => {
    expect(typeof push).toBe('function')
    expect(typeof dismiss).toBe('function')
    expect(typeof clear).toBe('function')
  })

  it('renders all four semantic variants', async () => {
    const wrapper = mount(Toaster)
    for (const variant of VARIANTS) push({ message: `${variant} message`, variant })
    await nextTick()

    const items = wrapper.findAll('.toast')
    expect(items).toHaveLength(4)
    for (const variant of VARIANTS) {
      expect(wrapper.find(`.toast--${variant}`).exists()).toBe(true)
    }
    expect(toasts.value.map((toast) => toast.variant)).toEqual(VARIANTS)
    expect(wrapper.text()).toContain('info message')
    expect(wrapper.text()).toContain('error message')
  })

  it('accepts the shorthand push(message, variant) form', async () => {
    const wrapper = mount(Toaster)
    push('short form', 'success')
    await nextTick()

    expect(wrapper.get('.toast--success').text()).toContain('short form')
  })

  it('stacks toasts in insertion order', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'first' })
    push({ message: 'second' })
    push({ message: 'third' })
    await nextTick()

    const messages = wrapper.findAll('.toast__message').map((node) => node.text())
    expect(messages).toEqual(['first', 'second', 'third'])
  })

  it('auto-dismisses after the configured duration', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'temporary', variant: 'info', duration: 1000 })
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(1)

    vi.advanceTimersByTime(999)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(1)

    vi.advanceTimersByTime(1)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(0)
  })

  it('uses the default duration for auto-dismiss', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'default' })
    await nextTick()

    vi.advanceTimersByTime(DEFAULT_TOAST_DURATION - 1)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(1)

    vi.advanceTimersByTime(1)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(0)
  })

  it('keeps duration: 0 toasts until dismissed manually', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'persistent', duration: 0 })
    await nextTick()

    vi.advanceTimersByTime(DEFAULT_TOAST_DURATION * 10)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(1)
  })

  it('dismisses a single toast via the keyboard-operable close button', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'first', duration: 0 })
    push({ message: 'second', duration: 0 })
    await nextTick()

    const closeButtons = wrapper.findAll('button.toast__close')
    expect(closeButtons).toHaveLength(2)
    expect(closeButtons[0].attributes('aria-label')).toMatch(/dismiss info notification/i)

    await closeButtons[0].trigger('click')
    await nextTick()

    expect(wrapper.findAll('.toast')).toHaveLength(1)
    expect(wrapper.text()).not.toContain('first')
    expect(wrapper.text()).toContain('second')
  })

  it('removes every toast with clear()', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'a', duration: 0 })
    push({ message: 'b', duration: 0 })
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(2)

    clear()
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(0)
  })

  it('dismisses programmatically by id', async () => {
    const wrapper = mount(Toaster)
    const id = push({ message: 'by id', duration: 0 })
    await nextTick()
    expect(toasts.value.map((toast) => toast.id)).toContain(id)

    dismiss(id)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(0)
  })

  it('pauses auto-dismiss while hovered and resumes on leave', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'hover me', duration: 1000 })
    await nextTick()

    const item = wrapper.get('.toast')
    await item.trigger('mouseenter')
    vi.advanceTimersByTime(5000)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(1)

    await item.trigger('mouseleave')
    vi.advanceTimersByTime(1000)
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(0)
  })
})

describe('Toaster accessibility audit — FE-010 T2 (axe-equivalent)', () => {
  beforeEach(() => {
    clear()
    vi.useFakeTimers()
  })

  afterEach(() => {
    clear()
    vi.useRealTimers()
  })

  it('always renders a persistent aria-live region', () => {
    const wrapper = mount(Toaster)
    const live = wrapper.find('[aria-live]')
    expect(live.exists()).toBe(true)
    expect(live.attributes('aria-live')).toBe('polite')
    // The region must exist in the DOM even when empty for AT to observe changes.
    expect(wrapper.find('.toaster__list').exists()).toBe(true)
  })

  it('announces each toast with status/alert roles and labels every control', async () => {
    const wrapper = mount(Toaster)
    push({ message: 'ok', variant: 'success' })
    push({ message: 'bad', variant: 'error' })
    await nextTick()

    const items = wrapper.findAll('.toast')
    expect(items[0].attributes('role')).toBe('status')
    expect(items[1].attributes('role')).toBe('alert')

    for (const button of wrapper.findAll('button.toast__close')) {
      expect(button.attributes('aria-label')).toBeTruthy()
    }
    // Decorative glyphs are hidden from assistive tech.
    expect(wrapper.find('.toast__icon').attributes('aria-hidden')).toBe('true')
  })

  it('keeps text semantically coloured via AA tokens (no raw hex, no glow)', async () => {
    const wrapper = mount(Toaster)
    for (const variant of VARIANTS) push({ message: variant, variant })
    await nextTick()
    expect(wrapper.findAll('.toast')).toHaveLength(4)

    // FE-014 constraints: no raw hex / glows in component styles.
    const source = readFileSync(join(process.cwd(), 'src/components/Toaster.vue'), 'utf8')
    expect(source).not.toMatch(/#[0-9a-fA-F]{3,6}\b/)
    expect(source).not.toMatch(/text-shadow|drop-shadow|blur\(/)

    // Token-level contrast stands in for a browser axe check (PROTOCOL §6).
    const tokens = readFileSync(join(process.cwd(), 'src/assets/styles/tokens.css'), 'utf8')
    const dark = vars(tokens, ':root {')
    const light = vars(tokens, ":root[data-theme='light']")
    // `error` is rendered from the `danger` semantic token family.
    const TOKEN: Record<ToastVariant, string> = {
      info: 'info',
      success: 'success',
      warning: 'warning',
      error: 'danger',
    }
    for (const theme of [dark, light]) {
      for (const variant of VARIANTS) {
        const fg = theme[`--color-${TOKEN[variant]}-text`]
        const bg = theme['--color-elevated']
        expect(fg).toBeTruthy()
        expect(contrast(fg, bg)).toBeGreaterThanOrEqual(4.5)
      }
      expect(contrast(theme['--color-text'], theme['--color-elevated'])).toBeGreaterThanOrEqual(4.5)
    }
  })
})

function vars(css: string, selector: string): Record<string, string> {
  const start = css.indexOf(selector)
  if (start < 0) throw new Error(`selector not found: ${selector}`)
  const open = css.indexOf('{', start)
  let depth = 0
  let end = open
  for (let i = open; i < css.length; i += 1) {
    if (css[i] === '{') depth += 1
    else if (css[i] === '}') {
      depth -= 1
      if (depth === 0) {
        end = i
        break
      }
    }
  }
  const body = css.slice(open + 1, end)
  const out: Record<string, string> = {}
  const re = /(--[a-z0-9-]+)\s*:\s*([^;]+);/gi
  let match: RegExpExecArray | null
  while ((match = re.exec(body))) out[match[1]] = match[2].trim()
  return out
}

function channel(value: number): number {
  const c = value / 255
  return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
}

function luminance(hex: string): number {
  const clean = hex.replace('#', '')
  const full =
    clean.length === 3
      ? clean
          .split('')
          .map((c) => c + c)
          .join('')
      : clean
  const r = parseInt(full.slice(0, 2), 16)
  const g = parseInt(full.slice(2, 4), 16)
  const b = parseInt(full.slice(4, 6), 16)
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)
}

function contrast(foreground: string, background: string): number {
  const a = luminance(foreground)
  const b = luminance(background)
  const [hi, lo] = a > b ? [a, b] : [b, a]
  return (hi + 0.05) / (lo + 0.05)
}
