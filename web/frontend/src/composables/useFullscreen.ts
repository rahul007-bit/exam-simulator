import { computed, getCurrentInstance, onBeforeUnmount, onMounted, readonly, ref, toValue, watch } from 'vue'
import type { MaybeRefOrGetter } from 'vue'

/**
 * Fullscreen anti-cheat composable (FE-028).
 *
 * Ports the legacy fullscreen guard:
 *   - `enterCandidateFullscreen` — enter on exam start
 *   - `showFullscreenWarning`    — lock overlay on exit
 *   - `requestKeyboardLock`      — Keyboard Lock API where supported
 *   - `releaseKeyboardLock`
 *   - `initFullscreenGuard`       — fullscreenchange + input guards
 *
 * All browser-specific behaviour is isolated here (PLAN §7 "Fullscreen/keyboard-lock
 * browser fragility"). Every capability is feature-detected, and every async call is
 * wrapped so an unsupported/denied browser degrades without breaking the exam.
 *
 * Like `useToast`/`useTheme` the reactive state is module-level. That lets the
 * `FullscreenGuard.vue` overlay read `warningVisible` while the candidate view
 * drives entry via `useFullscreen({ isAdmin, isActive })` — both observe the same
 * singleton without prop/event plumbing.
 *
 * Browser notes:
 *   - Chrome/Edge implement `Element.requestFullscreen()` + `navigator.keyboard.lock()`.
 *     Keyboard Lock needs a fullscreen document + user activation; if it rejects we
 *     swallow it and keep the exam usable.
 *   - Firefox implements fullscreen but historically not `navigator.keyboard`
 *     (Keyboard Lock is unshipped/behind a pref). `getKeyboard()` returns null and
 *     the lock is simply skipped.
 *   - Safari uses the `webkit*` prefixed methods; those are handled but resolve
 *     synchronously, so we never rely on the returned promise.
 */

/** Structural view of the (not always typed) Keyboard Lock API on `navigator`. */
interface KeyboardLock {
  lock?: (keyCodes?: string[]) => Promise<void>
  unlock?: () => void
}

/** Prefixed fullscreen surface kept off the standard `Element` type. */
type FullscreenElement = Element & {
  webkitRequestFullscreen?: () => Promise<void> | void
}

/** Prefixed `document` surface (Safari/older WebKit). */
type FullscreenDocument = Document & {
  webkitFullscreenElement?: Element | null
  webkitExitFullscreen?: () => Promise<void> | void
}

/** DevTools hotkeys blocked for candidates (legacy guard). */
const DEVTOOLS_KEYS = ['I', 'i', 'J', 'j', 'C', 'c']

const isFullscreen = ref(false)
const warningVisible = ref(false)
const keyboardLockActive = ref(false)

let policyIsAdmin: () => boolean = () => false
let policyIsActive: () => boolean = () => false
let policyTarget: () => Element | null = () =>
  typeof document !== 'undefined' ? document.documentElement : null

let listenersAttached = false
let entering = false

function getDoc(): FullscreenDocument | null {
  return typeof document === 'undefined' ? null : (document as FullscreenDocument)
}

function getKeyboard(): KeyboardLock | null {
  if (typeof navigator === 'undefined') return null
  const keyboard = (navigator as Navigator & { keyboard?: KeyboardLock }).keyboard
  return keyboard ?? null
}

/** The element currently in fullscreen, across standard + WebKit prefixes. */
function fullscreenElement(): Element | null {
  const doc = getDoc()
  if (!doc) return null
  return doc.fullscreenElement ?? doc.webkitFullscreenElement ?? null
}

/** Resolve a request function for `el`, or null when fullscreen is unsupported. */
function requestFullscreenFn(el: Element): (() => Promise<void> | void) | null {
  const target = el as FullscreenElement
  if (typeof target.requestFullscreen === 'function') return () => target.requestFullscreen()
  if (typeof target.webkitRequestFullscreen === 'function') {
    return () => target.webkitRequestFullscreen?.()
  }
  return null
}

/** Whether this browser exposes a usable fullscreen entry point. */
export function isFullscreenSupported(): boolean {
  if (typeof document === 'undefined') return false
  const el = (document.documentElement ?? null) as FullscreenElement | null
  if (!el) return false
  return typeof el.requestFullscreen === 'function' || typeof el.webkitRequestFullscreen === 'function'
}

/** Whether `navigator.keyboard.lock()` is available (Chrome/Edge, not Firefox). */
export function isKeyboardLockSupported(): boolean {
  const keyboard = getKeyboard()
  return keyboard !== null && typeof keyboard.lock === 'function'
}

/** Lock the whole keyboard (Escape/Tab delivered to the terminal) where supported. */
export async function requestKeyboardLock(): Promise<boolean> {
  const keyboard = getKeyboard()
  if (!keyboard || typeof keyboard.lock !== 'function') return false
  try {
    await keyboard.lock()
    keyboardLockActive.value = true
    return true
  } catch {
    keyboardLockActive.value = false
    return false
  }
}

/** Release the keyboard lock; safe to call when unsupported or already released. */
export function releaseKeyboardLock(): void {
  const keyboard = getKeyboard()
  if (keyboard && typeof keyboard.unlock === 'function') {
    try {
      keyboard.unlock()
    } catch {
      /* already released */
    }
  }
  keyboardLockActive.value = false
}

/** Enter fullscreen on the configured target. Resolves `false` on any failure. */
export async function enterFullscreen(): Promise<boolean> {
  const target = policyTarget()
  if (!target) return false

  entering = true
  try {
    if (!fullscreenElement()) {
      const request = requestFullscreenFn(target)
      if (!request) return false
      await request()
    }
    isFullscreen.value = true
    warningVisible.value = false
    void requestKeyboardLock()
    return true
  } catch {
    return false
  } finally {
    entering = false
  }
}

/** Exit fullscreen; the `fullscreenchange` handler drives the warning overlay. */
export async function exitFullscreen(): Promise<void> {
  const doc = getDoc()
  if (!doc) return
  try {
    const webkitExit = doc.webkitExitFullscreen
    if (typeof doc.exitFullscreen === 'function') await doc.exitFullscreen()
    else if (typeof webkitExit === 'function') await webkitExit.call(doc)
  } catch {
    /* not in fullscreen, or the request was denied */
  }
}

/** Toggle fullscreen; used by the admin/overflow "Fullscreen" action. */
export async function toggleFullscreen(): Promise<void> {
  if (fullscreenElement()) await exitFullscreen()
  else await enterFullscreen()
}

/** Enforcement applies only to a non-admin candidate with a live exam. */
export function shouldEnforceFullscreen(): boolean {
  return !policyIsAdmin() && policyIsActive()
}

/** Show the lock overlay when the exam is active, enforced and not fullscreen. */
export function showWarningIfNeeded(): void {
  if (entering) return
  if (fullscreenElement()) {
    warningVisible.value = false
    return
  }
  warningVisible.value = shouldEnforceFullscreen()
}

/** Hide the overlay without changing fullscreen state. */
export function hideWarning(): void {
  warningVisible.value = false
}

/** Return-to-fullscreen action for the overlay (user gesture preserving). */
export async function reenterFullscreen(): Promise<boolean> {
  hideWarning()
  return enterFullscreen()
}

function handleFullscreenChange(): void {
  const active = fullscreenElement() !== null
  isFullscreen.value = active
  if (active) {
    warningVisible.value = false
    void requestKeyboardLock()
  } else {
    releaseKeyboardLock()
    showWarningIfNeeded()
  }
}

function handleContextMenu(event: MouseEvent): void {
  if (!shouldEnforceFullscreen()) return
  event.preventDefault()
}

function handleKeydown(event: KeyboardEvent): void {
  if (!shouldEnforceFullscreen()) return
  if (event.key === 'F12' || (event.ctrlKey && event.shiftKey && DEVTOOLS_KEYS.includes(event.key))) {
    event.preventDefault()
  }
}

/** Attach the global `fullscreenchange` (+ candidate input) listeners once. */
export function startFullscreenGuard(): void {
  if (listenersAttached) return
  const doc = getDoc()
  if (!doc) return
  doc.addEventListener('fullscreenchange', handleFullscreenChange)
  doc.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  doc.addEventListener('contextmenu', handleContextMenu)
  doc.addEventListener('keydown', handleKeydown)
  isFullscreen.value = fullscreenElement() !== null
  listenersAttached = true
}

/** Detach the global listeners and reset transient lock state. */
export function stopFullscreenGuard(): void {
  if (!listenersAttached) return
  const doc = getDoc()
  if (doc) {
    doc.removeEventListener('fullscreenchange', handleFullscreenChange)
    doc.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
    doc.removeEventListener('contextmenu', handleContextMenu)
    doc.removeEventListener('keydown', handleKeydown)
  }
  releaseKeyboardLock()
  listenersAttached = false
}

export interface UseFullscreenOptions {
  /** Admin bypass — admins are never locked or warned (default `false`). */
  isAdmin?: MaybeRefOrGetter<boolean>
  /** Whether an exam session is live; the overlay only shows while active. */
  isActive?: MaybeRefOrGetter<boolean>
  /** Fullscreen target; defaults to `document.documentElement`. */
  target?: () => Element | null
  /** Attach listeners on mount. Default `true`. */
  autoStart?: boolean
}

/**
 * Shared fullscreen guard. Call from a component setup:
 *
 *   const fs = useFullscreen({ isAdmin: computed(() => session.isAdmin), isActive: active })
 *   // on the Start click (user gesture): fs.enter()
 */
export function useFullscreen(options: UseFullscreenOptions = {}) {
  const isAdminOption = options.isAdmin
  const isActiveOption = options.isActive

  if (isAdminOption !== undefined) policyIsAdmin = () => toValue(isAdminOption)
  if (isActiveOption !== undefined) policyIsActive = () => toValue(isActiveOption)
  if (options.target !== undefined) policyTarget = options.target

  const inComponent = getCurrentInstance() !== null

  if (inComponent && (isAdminOption !== undefined || isActiveOption !== undefined)) {
    watch(
      () => [toValue(isAdminOption), toValue(isActiveOption)],
      () => showWarningIfNeeded(),
    )
  }

  if (options.autoStart !== false) {
    if (inComponent) onMounted(startFullscreenGuard)
    else startFullscreenGuard()
  }

  if (inComponent) onBeforeUnmount(stopFullscreenGuard)

  return {
    isFullscreen: readonly(isFullscreen),
    warningVisible: readonly(warningVisible),
    keyboardLockActive: readonly(keyboardLockActive),
    supported: computed(isFullscreenSupported),
    keyboardLockSupported: computed(isKeyboardLockSupported),
    enter: enterFullscreen,
    exit: exitFullscreen,
    toggle: toggleFullscreen,
    reenter: reenterFullscreen,
    hideWarning,
    requestKeyboardLock,
    releaseKeyboardLock,
  }
}
