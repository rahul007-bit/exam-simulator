import { mount, type VueWrapper } from '@vue/test-utils'
import { nextTick } from 'vue'
import { afterEach, describe, expect, it } from 'vitest'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { cancel, confirm, prompt, useConfirm } from '@/composables/useConfirm'

// Headless UI's <Dialog> observes its panel with ResizeObserver; jsdom does not
// implement it. Shim it locally so the dialog can mount in the unit environment.
if (!('ResizeObserver' in globalThis)) {
  class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  ;(globalThis as { ResizeObserver?: unknown }).ResizeObserver = ResizeObserverStub
}

const { active } = useConfirm()

let wrapper: VueWrapper | null = null

function mountHost(): void {
  wrapper = mount(ConfirmDialog, { attachTo: document.body })
}

async function tick(times = 2): Promise<void> {
  for (let i = 0; i < times; i += 1) await nextTick()
}

function q<T extends Element = HTMLElement>(selector: string): T {
  const node = document.body.querySelector<T>(selector)
  if (!node) throw new Error(`expected element not found: ${selector}`)
  return node
}

async function waitFor<T extends Element = HTMLElement>(
  selector: string,
  attempts = 40,
): Promise<T> {
  for (let i = 0; i < attempts; i += 1) {
    const node = document.body.querySelector<T>(selector)
    if (node) return node
    await nextTick()
    await new Promise((resolve) => setTimeout(resolve, 0))
  }
  throw new Error(`timed out waiting for ${selector}`)
}

function typeInto(input: HTMLInputElement, value: string): void {
  input.value = value
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

afterEach(async () => {
  while (active.value) cancel()
  await tick()
  wrapper?.unmount()
  wrapper = null
  document.getElementById('headlessui-portal-root')?.remove()
})

describe('useConfirm + ConfirmDialog — FE-011 T1', () => {
  it('confirm() resolves true when the confirm button is activated', async () => {
    mountHost()
    const result = confirm({ title: 'Delete preset', message: 'This cannot be undone.' })
    await tick()

    expect(active.value?.kind).toBe('confirm')
    expect(q('[data-testid="dialog-panel"]')).toBeTruthy()
    expect(document.body.textContent).toContain('Delete preset')
    expect(document.body.textContent).toContain('This cannot be undone.')

    q<HTMLButtonElement>('[data-testid="confirm"]').click()
    await tick()

    await expect(result).resolves.toBe(true)
    expect(active.value).toBeNull()
    expect(document.body.querySelector('[data-testid="dialog-panel"]')).toBeNull()
  })

  it('confirm() resolves false when cancelled', async () => {
    mountHost()
    const result = confirm({ title: 'Discard changes' })
    await tick()

    q<HTMLButtonElement>('[data-testid="cancel"]').click()
    await tick()

    await expect(result).resolves.toBe(false)
    expect(active.value).toBeNull()
  })

  it('confirm() resolves false on Escape', async () => {
    mountHost()
    const result = confirm({ title: 'Escape me' })
    await tick()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await tick()

    await expect(result).resolves.toBe(false)
    expect(active.value).toBeNull()
  })

  it('prompt() resolves the entered value on confirm', async () => {
    mountHost()
    const result = prompt({ title: 'Session name', defaultValue: 'sess-1' })
    await tick()

    const input = q<HTMLInputElement>('[data-testid="prompt-input"]')
    expect(input.value).toBe('sess-1')

    typeInto(input, 'sess-42')
    await tick()
    q<HTMLButtonElement>('[data-testid="confirm"]').click()
    await tick()

    await expect(result).resolves.toBe('sess-42')
    expect(active.value).toBeNull()
  })

  it('prompt() resolves null when cancelled', async () => {
    mountHost()
    const result = prompt({ title: 'Session name', message: 'Name?' })
    await tick()

    q<HTMLButtonElement>('[data-testid="cancel"]').click()
    await tick()

    await expect(result).resolves.toBeNull()
    expect(active.value).toBeNull()
  })

  it('queues concurrent requests and resolves them in order (FIFO)', async () => {
    mountHost()
    const first = confirm({ title: 'First' })
    await tick()
    const second = prompt({ title: 'Second', defaultValue: 'queued' })
    await tick()

    expect(active.value?.title).toBe('First')
    q<HTMLButtonElement>('[data-testid="confirm"]').click()
    await tick()
    await expect(first).resolves.toBe(true)

    expect(active.value?.title).toBe('Second')
    ;(await waitFor<HTMLButtonElement>('[data-testid="confirm"]')).click()
    await tick()
    await expect(second).resolves.toBe('queued')
    expect(active.value).toBeNull()
  })

  it('exposes a labelled, modal dialog (aria-wiring from Headless UI)', async () => {
    mountHost()
    const result = confirm({ title: 'Remove node', message: 'Remove node-1?' })
    await tick()

    const root = q('[data-testid="dialog-root"]')
    expect(root.getAttribute('role')).toBe('dialog')
    expect(root.getAttribute('aria-modal')).toBe('true')

    const labelledby = root.getAttribute('aria-labelledby')
    expect(labelledby).toBeTruthy()
    expect(document.getElementById(labelledby as string)?.textContent).toContain('Remove node')

    const describedby = root.getAttribute('aria-describedby')
    expect(describedby).toBeTruthy()
    expect(document.getElementById(describedby as string)?.textContent).toContain('Remove node-1?')

    cancel()
    await expect(result).resolves.toBe(false)
  })

  it('focusses the confirm button initially', async () => {
    mountHost()
    const result = confirm({ title: 'Focus' })
    await tick(4)

    expect(document.activeElement).toBe(q('[data-testid="confirm"]'))

    cancel()
    await expect(result).resolves.toBe(false)
  })
})
