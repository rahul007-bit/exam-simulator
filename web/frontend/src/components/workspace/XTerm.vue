<script setup lang="ts">
import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import type { ITheme } from '@xterm/xterm'
import { onBeforeUnmount, onMounted, shallowRef, useTemplateRef, watch } from 'vue'

import { useTerminal } from '@/composables/useTerminal'

import '@xterm/xterm/css/xterm.css'

/**
 * XTerm island (FE-025).
 *
 * Wraps `@xterm/xterm` + `@xterm/addon-fit` as an imperative island: the
 * terminal and socket live in refs, never in reactive state. Columns/rows come
 * from the fit addon; `useTerminal` turns a resize into the exact JSON frame the
 * server expects. Colours are read from the design tokens at mount so the
 * container stays within the "no raw hex" rule (FE-002/FE-014).
 */

const props = withDefaults(
  defineProps<{
    sessionId: string
    autoConnect?: boolean
    ariaLabel?: string
  }>(),
  { autoConnect: true, ariaLabel: 'Terminal' },
)

const containerRef = useTemplateRef<HTMLDivElement>('container')
const terminalRef = shallowRef<Terminal | null>(null)
const fitAddonRef = shallowRef<FitAddon | null>(null)

let resizeObserver: ResizeObserver | null = null
let connectFrame: number | null = null

function readToken(name: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return value.length > 0 ? value : fallback
}

function buildTheme(): ITheme {
  return {
    background: readToken('--color-bg-app', 'transparent'),
    foreground: readToken('--color-text', ''),
    cursor: readToken('--color-accent', ''),
    cursorAccent: readToken('--color-bg-app', ''),
    selectionBackground: readToken('--color-hover', ''),
    black: readToken('--color-bg-app', ''),
    red: readToken('--color-danger', ''),
    green: readToken('--color-success', ''),
    yellow: readToken('--color-warning', ''),
    blue: readToken('--color-info', ''),
    magenta: readToken('--color-accent', ''),
    cyan: readToken('--color-info', ''),
    white: readToken('--color-text', ''),
    brightBlack: readToken('--color-text-dim', ''),
    brightRed: readToken('--color-danger-text', ''),
    brightGreen: readToken('--color-success-text', ''),
    brightYellow: readToken('--color-warning-text', ''),
    brightBlue: readToken('--color-info-text', ''),
    brightMagenta: readToken('--color-accent-text', ''),
    brightCyan: readToken('--color-info-text', ''),
    brightWhite: readToken('--color-text', ''),
  }
}

const {
  status,
  connected,
  connect,
  disconnect,
  reconnect,
  send,
  sendResize,
  replayScrollback,
  getScrollback,
  clearScrollback,
} = useTerminal({
  sessionId: () => props.sessionId,
  terminal: terminalRef,
  onOpen: () => {
    fitTerminal()
    sendResize()
  },
})

function fitTerminal(): void {
  const fitAddon = fitAddonRef.value
  if (!fitAddon) return
  try {
    fitAddon.fit()
  } catch {
    /* hidden or zero-size container; the next resize re-fits */
  }
}

function handleWindowResize(): void {
  fitTerminal()
}

function observeContainer(container: HTMLDivElement): void {
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => fitTerminal())
    resizeObserver.observe(container)
  }
  window.addEventListener('resize', handleWindowResize)
}

onMounted(() => {
  const container = containerRef.value
  if (!container) return

  const term = new Terminal({
    cursorBlink: true,
    fontFamily: readToken('--font-mono', 'monospace'),
    fontSize: 14,
    lineHeight: 1.25,
    scrollback: 5000,
    theme: buildTheme(),
  })
  terminalRef.value = term

  const fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  fitAddonRef.value = fitAddon

  term.open(container)
  observeContainer(container)

  connectFrame = window.requestAnimationFrame(() => {
    connectFrame = null
    fitTerminal()
    if (props.autoConnect) connect()
  })
})

watch(
  () => props.sessionId,
  (next, previous) => {
    if (next === previous || !terminalRef.value) return
    if (props.autoConnect) {
      disconnect()
      connect()
    }
  },
)

onBeforeUnmount(() => {
  disconnect()
  if (connectFrame !== null) {
    window.cancelAnimationFrame(connectFrame)
    connectFrame = null
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  window.removeEventListener('resize', handleWindowResize)

  const term = terminalRef.value
  terminalRef.value = null
  fitAddonRef.value = null
  try {
    term?.dispose()
  } catch {
    /* already disposed */
  }
})

defineExpose({
  status,
  connected,
  connect,
  disconnect,
  reconnect,
  send,
  sendResize,
  replayScrollback,
  getScrollback,
  clearScrollback,
  fit: fitTerminal,
})
</script>

<template>
  <div
    ref="container"
    class="h-full w-full overflow-hidden rounded-[var(--radius-md)] border border-border bg-app p-1"
    role="group"
    :aria-label="ariaLabel"
    data-testid="xterm-container"
  ></div>
</template>
