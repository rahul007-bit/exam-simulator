<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, watch } from 'vue'

import { useClipboard } from '@/composables/useClipboard'
import { useToast } from '@/composables/useToast'
import { useVnc } from '@/composables/useVnc'

/**
 * ClipboardBridge (FE-027) — headless host <-> noVNC clipboard bridge.
 *
 * Mounts every browser listener the legacy candidate client registered
 * (`web/static/js/app.js:99-179`) and wires them to `useClipboard`:
 *
 *   - `click` / `pointerdown` / `keydown` (capture, passive) flush a clipboard
 *     write that was blocked for lack of a user gesture (`app.js:120-130`);
 *   - `copy` reads the host clipboard and pushes it to the desktop (`app.js:170`);
 *   - `visibilitychange` / `focus` resync from the desktop when the WS is down
 *     (`app.js:99-111`);
 *   - `VNC_CLIPBOARD` window messages from the noVNC island feed the host
 *     clipboard (`app.js:156-159`).
 *
 * It renders nothing meaningful: the hidden `<span>` keeps the component inert
 * and gives integrations a stable `data-testid` hook. Disposed on unmount.
 *
 * Integration: the orchestrator renders it next to the workspace tab host and
 * passes the live noVNC `<iframe>` via `iframe` (e.g. the `frame` exposed by
 * `NoVncFrame`/`WorkspaceTabs`). When omitted it discovers the island by its
 * `data-testid="novnc-frame"` marker. To multiplex an already-open session
 * socket instead of connecting its own, set `:auto-connect="false"` and call
 * the exposed `handleMessage()` with each raw `/ws/session/<id>` frame.
 */

const props = withDefaults(
  defineProps<{
    sessionId?: string | null
    /** Whether the session is active (gates the disconnected fallback poll). */
    active?: boolean
    /** The noVNC `<iframe>` to bridge with (falls back to a DOM lookup). */
    iframe?: HTMLIFrameElement | null
    /** Open a `/ws/session/<id>` socket. Disable to feed frames via `handleMessage`. */
    autoConnect?: boolean
  }>(),
  { sessionId: null, active: true, iframe: null, autoConnect: true },
)

const emit = defineEmits<{
  'desktop-clipboard': [text: string, explicit: boolean]
}>()

const { push } = useToast()

function onDesktopClipboard(text: string, explicit: boolean): void {
  if (!text) return
  const clean = text.replace(/[\r\n\t]+/g, ' ').trim()
  const snippet = clean.length > 32 ? `${clean.slice(0, 29)}...` : clean
  if (explicit) {
    push({ variant: 'success', message: `Copied from Desktop: "${snippet}"` })
  } else {
    push({ variant: 'info', message: `Desktop clipboard: "${snippet}" — click anywhere to copy` })
  }
  emit('desktop-clipboard', text, explicit)
}

function onEmpty(): void {
  push({ variant: 'info', message: 'Desktop clipboard is empty' })
}

/** Resolve the live noVNC iframe (prop first, then the island's test id). */
function resolveFrame(): HTMLIFrameElement | null {
  if (props.iframe) return props.iframe
  if (typeof document === 'undefined') return null
  return document.querySelector<HTMLIFrameElement>('iframe[data-testid="novnc-frame"]')
}

const clipboard = useClipboard({
  sessionId: () => props.sessionId,
  active: () => props.active,
  frame: resolveFrame,
  autoConnect: false,
  onDesktopClipboard,
  onEmpty,
})

// Inbound noVNC -> host. `useVnc` starts/stops its own listener on mount/unmount.
const vnc = useVnc({
  onClipboard: (text) => {
    void clipboard.handleVncClipboard(text, false)
  },
})

watch(
  () => props.iframe,
  (frame) => vnc.setSource(frame ?? resolveFrame()),
  { immediate: true },
)

const FLUSH_EVENTS = ['click', 'pointerdown', 'keydown'] as const

function onUserGesture(): void {
  clipboard.flushPendingHostClipboard()
}

function onCopy(): void {
  clipboard.syncHostClipboard()
}

function onVisibilityChange(): void {
  if (document.visibilityState === 'visible') maybeSyncFromVnc()
}

function onWindowFocus(): void {
  maybeSyncFromVnc()
}

function maybeSyncFromVnc(): void {
  if (!props.active || clipboard.connected.value) return
  void clipboard.syncFromVnc(false)
}

// The session store hydrates *after* this component mounts (`main.ts` runs
// `initAppStores` non-blocking), so the real session id can arrive late. Rebind
// the clipboard socket whenever the id (or `active`) changes, instead of
// connecting once to a stale `/ws/session/active` and never reconnecting.
watch(
  () => [props.sessionId, props.active] as const,
  ([sessionId, active]) => {
    clipboard.stop()
    if (active && sessionId) clipboard.start()
    // The noVNC island only renders once the session is active, so re-resolve
    // its window after the DOM updates to scope inbound `VNC_CLIPBOARD` events.
    void nextTick(() => vnc.setSource(resolveFrame()))
  },
  { immediate: true },
)

onMounted(() => {
  vnc.setSource(resolveFrame())

  for (const event of FLUSH_EVENTS) {
    document.addEventListener(event, onUserGesture, { capture: true, passive: true })
  }
  document.addEventListener('copy', onCopy)
  document.addEventListener('visibilitychange', onVisibilityChange)
  window.addEventListener('focus', onWindowFocus)
})

onBeforeUnmount(() => {
  for (const event of FLUSH_EVENTS) {
    document.removeEventListener(event, onUserGesture, { capture: true })
  }
  document.removeEventListener('copy', onCopy)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  window.removeEventListener('focus', onWindowFocus)
  clipboard.stop()
})

defineExpose({
  clipboard,
  handleMessage: clipboard.handleMessage,
  sendToVnc: clipboard.sendToVnc,
  copyFromDesktopToHost: clipboard.copyFromDesktopToHost,
  flushPendingHostClipboard: clipboard.flushPendingHostClipboard,
})
</script>

<template>
  <span hidden aria-hidden="true" data-testid="clipboard-bridge"></span>
</template>
