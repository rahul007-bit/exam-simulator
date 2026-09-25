import { readonly, ref } from 'vue'
import type { Ref } from 'vue'

export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'cka:theme'
const THEME_ATTR = 'data-theme'

function isTheme(value: unknown): value is Theme {
  return value === 'dark' || value === 'light'
}

function mediaQuery(): MediaQueryList | null {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return null
  return window.matchMedia('(prefers-color-scheme: light)')
}

function readStored(): Theme | null {
  if (typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return isTheme(raw) ? raw : null
  } catch {
    return null
  }
}

/** Theme to use when the user has not made an explicit, persisted choice. */
export function preferredTheme(): Theme {
  const stored = readStored()
  if (stored) return stored
  return mediaQuery()?.matches ? 'light' : 'dark'
}

/** Apply a theme to <html> (also hints the native `color-scheme`). */
export function applyTheme(theme: Theme): void {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute(THEME_ATTR, theme)
  document.documentElement.style.colorScheme = theme
}

const current: Ref<Theme> = ref('dark')
let initialised = false

/** Initialise from persisted choice, else the OS preference; track OS changes. */
export function initTheme(): void {
  current.value = preferredTheme()
  applyTheme(current.value)

  if (initialised) return
  initialised = true

  const media = mediaQuery()
  media?.addEventListener?.('change', () => {
    if (readStored()) return
    current.value = media.matches ? 'light' : 'dark'
    applyTheme(current.value)
  })
}

/** Persist and apply an explicit theme choice. */
export function setTheme(theme: Theme): void {
  current.value = theme
  applyTheme(theme)
  try {
    window.localStorage.setItem(STORAGE_KEY, theme)
  } catch {
    /* storage may be unavailable (private mode); theme still applies */
  }
}

/** Drop the manual choice and fall back to the OS preference. */
export function clearTheme(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    /* ignore */
  }
  current.value = preferredTheme()
  applyTheme(current.value)
}

/** Flip between dark and light, persisting the new choice. */
export function toggleTheme(): void {
  setTheme(current.value === 'dark' ? 'light' : 'dark')
}

export function useTheme() {
  return {
    theme: readonly(current),
    setTheme,
    toggleTheme,
    clearTheme,
  }
}
