import { beforeEach, describe, expect, it, vi } from 'vitest'

const STORAGE_KEY = 'cka:theme'

function mockMatchMedia(initial: boolean) {
  const listeners: Array<() => void> = []
  const mql = {
    matches: initial,
    media: '(prefers-color-scheme: light)',
    onchange: null,
    addEventListener: (_type: string, cb: () => void) => listeners.push(cb),
    removeEventListener: () => {},
    addListener: (cb: () => void) => listeners.push(cb),
    removeListener: () => {},
    dispatchEvent: () => true,
  }
  window.matchMedia = vi.fn().mockReturnValue(mql) as unknown as typeof window.matchMedia
  return {
    setMatches(value: boolean) {
      mql.matches = value
    },
    emit() {
      listeners.forEach((cb) => cb())
    },
  }
}

async function freshThemeModule() {
  vi.resetModules()
  return import('@/composables/useTheme')
}

function currentTheme(): string | null {
  return document.documentElement.getAttribute('data-theme')
}

describe('theme: prefers-color-scheme default + persisted manual toggle', () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    document.documentElement.style.colorScheme = ''
  })

  it('defaults to the OS preference when nothing is stored', async () => {
    mockMatchMedia(true)
    const mod = await freshThemeModule()
    mod.initTheme()
    expect(currentTheme()).toBe('light')

    mockMatchMedia(false)
    const darkMod = await freshThemeModule()
    darkMod.initTheme()
    expect(currentTheme()).toBe('dark')
  })

  it('toggle flips data-theme and persists the choice (test T2)', async () => {
    mockMatchMedia(false)
    const { initTheme, toggleTheme } = await freshThemeModule()
    initTheme()
    expect(currentTheme()).toBe('dark')

    toggleTheme()
    expect(currentTheme()).toBe('light')
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('light')

    toggleTheme()
    expect(currentTheme()).toBe('dark')
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })

  it('persists across a reload and overrides the OS preference', async () => {
    mockMatchMedia(true)
    const first = await freshThemeModule()
    first.initTheme()
    expect(currentTheme()).toBe('light')
    first.setTheme('dark')

    mockMatchMedia(true)
    const second = await freshThemeModule()
    second.initTheme()
    expect(currentTheme()).toBe('dark')
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe('dark')
  })

  it('clearTheme drops the override and returns to the OS preference', async () => {
    mockMatchMedia(true)
    const { initTheme, setTheme, clearTheme } = await freshThemeModule()
    initTheme()
    setTheme('dark')
    expect(currentTheme()).toBe('dark')

    clearTheme()
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull()
    expect(currentTheme()).toBe('light')
  })

  it('follows OS changes while no manual choice exists', async () => {
    const os = mockMatchMedia(false)
    const { initTheme } = await freshThemeModule()
    initTheme()
    expect(currentTheme()).toBe('dark')

    os.setMatches(true)
    os.emit()
    expect(currentTheme()).toBe('light')
  })

  it('ignores OS changes after a manual choice', async () => {
    const os = mockMatchMedia(false)
    const { initTheme, setTheme } = await freshThemeModule()
    initTheme()
    setTheme('dark')

    os.setMatches(true)
    os.emit()
    expect(currentTheme()).toBe('dark')
  })

  it('exposes a reactive theme value', async () => {
    mockMatchMedia(false)
    const { initTheme, toggleTheme, useTheme } = await freshThemeModule()
    initTheme()
    const { theme } = useTheme()
    expect(theme.value).toBe('dark')
    toggleTheme()
    expect(theme.value).toBe('light')
  })
})
