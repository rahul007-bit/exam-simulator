import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ThemeToggle from '@/components/ThemeToggle.vue'
import { initTheme } from '@/composables/useTheme'

function mockMatchMedia(matches: boolean) {
  const mql = {
    matches,
    media: '(prefers-color-scheme: light)',
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => true,
  }
  window.matchMedia = vi.fn().mockReturnValue(mql) as unknown as typeof window.matchMedia
}

describe('ThemeToggle component (integration, stands in for browser e2e T2)', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    mockMatchMedia(false)
    initTheme()
  })

  it('clicking the button flips data-theme and persists it', async () => {
    const wrapper = mount(ThemeToggle)
    const button = wrapper.get('button')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(button.attributes('aria-label')).toMatch(/switch to light theme/i)

    await button.trigger('click')

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(window.localStorage.getItem('cka:theme')).toBe('light')

    await button.trigger('click')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(window.localStorage.getItem('cka:theme')).toBe('dark')
  })
})
