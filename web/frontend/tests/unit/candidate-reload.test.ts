/* eslint-disable vue/one-component-per-file -- this test intentionally defines
   lightweight stub components for the mount harness. */
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * FE-026/overflow wiring: the candidate header "Reload" action must match the
 * legacy `reloadWorkspaceFrame` (app.js:1726) — reconnect the terminal when the
 * terminal tab is active, otherwise force a fresh noVNC connection by reloading
 * the frame. `WorkspaceTabs` is stubbed so the test observes which imperative
 * handle `CandidateView.onAction('reload')` drives.
 */

const mocks = vi.hoisted(() => ({
  confirm: vi.fn(),
  push: vi.fn(),
  fullscreen: { enter: vi.fn(), exit: vi.fn(), toggle: vi.fn() },
  timer: { syncFromSession: vi.fn() },
  tabsState: { activeTab: 'desktop' as 'desktop' | 'terminal' },
  terminal: { reconnect: vi.fn() },
  vnc: { reload: vi.fn() },
  session: {
    isActive: true,
    isAdmin: false,
    isInvited: false,
    sessionId: 'sess-1' as string | null,
    data: { active: true, name: 'Test Exam' } as Record<string, unknown> | null,
    lockedPreset: null,
    currentTask: null,
    currentTaskNum: 1,
    totalTasks: 3,
    flaggedIds: [] as string[],
    loading: false,
    error: null as string | null,
    flag: vi.fn(),
    submit: vi.fn(),
    jump: vi.fn(),
    start: vi.fn(),
    reset: vi.fn(),
  },
  presets: {
    presets: [] as unknown[],
    selected: null,
    loading: false,
    error: null,
    fetchPresets: vi.fn(),
    selectPreset: vi.fn(),
  },
}))

vi.mock('vue-router', () => ({ useRoute: () => ({ query: {} }) }))
vi.mock('@/stores/session', () => ({ useSessionStore: () => mocks.session }))
vi.mock('@/stores/presets', () => ({ usePresetsStore: () => mocks.presets }))
vi.mock('@/stores/timer', () => ({ useTimerStore: () => mocks.timer }))
vi.mock('@/composables/useConfirm', () => ({ useConfirm: () => ({ confirm: mocks.confirm }) }))
vi.mock('@/composables/useToast', () => ({ useToast: () => ({ push: mocks.push }) }))
vi.mock('@/composables/useFullscreen', () => ({
  useFullscreen: () => mocks.fullscreen,
}))

// The recordings modal pulls in the replay player (xterm), whose module init
// touches canvas APIs jsdom does not implement; stub it away entirely.
vi.mock('@/components/candidate/RecordingsModal.vue', async () => {
  const { defineComponent: define, h: render } = await import('vue')
  return {
    default: define({
      name: 'RecordingsModal',
      props: { modelValue: { type: Boolean, default: false } },
      emits: ['update:modelValue'],
      setup: () => () => render('div'),
    }),
  }
})

// Replace the real workspace island (which pulls in xterm/noVNC) with a stub
// that exposes the same imperative handles `CandidateView` drives.
vi.mock('@/components/workspace/WorkspaceTabs.vue', async () => {
  const { computed, defineComponent: define, h: render } = await import('vue')
  return {
    default: define({
      name: 'WorkspaceTabs',
      props: {
        sessionId: { type: String, required: true },
        defaultTab: { type: String, default: 'desktop' },
        viewOnly: { type: Boolean, default: false },
        autoConnectTerminal: { type: Boolean, default: true },
      },
      setup(_props, { expose }) {
        expose({
          activeTab: computed(() => mocks.tabsState.activeTab),
          terminal: mocks.terminal,
          vnc: mocks.vnc,
        })
        return () => render('div', { 'data-testid': 'workspace-tabs' })
      },
    }),
  }
})

import CandidateView from '@/views/CandidateView.vue'

const AppShellStub = defineComponent({
  name: 'AppShell',
  emits: ['flag', 'submit', 'action', 'copy-session-id', 'select-task'],
  setup(_props, { slots }) {
    return () => h('div', { 'data-testid': 'app-shell' }, slots.default?.())
  },
})

const WorkspaceSplitStub = defineComponent({
  name: 'WorkspaceSplit',
  setup(_props, { slots }) {
    return () => h('div', [slots.left?.(), slots.default?.()])
  },
})

function mountView() {
  return mount(CandidateView, {
    global: {
      stubs: {
        AppShell: AppShellStub,
        WorkspaceSplit: WorkspaceSplitStub,
        TaskPane: true,
        ExamScorecard: true,
        PresetModal: true,
        RecordingsModal: true,
        FullscreenGuard: true,
        ClipboardBridge: true,
        Modal: true,
        Card: true,
        Button: true,
        Spinner: true,
      },
    },
  })
}

async function emitAction(wrapper: ReturnType<typeof mountView>, id: string): Promise<void> {
  wrapper.findComponent(AppShellStub).vm.$emit('action', id)
  await nextTick()
  await flushPromises()
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.tabsState.activeTab = 'desktop'
  mocks.session.isActive = true
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('CandidateView reload action', () => {
  it('reconnects the terminal when the terminal tab is active', async () => {
    const wrapper = mountView()
    mocks.tabsState.activeTab = 'terminal'

    await emitAction(wrapper, 'reload')

    expect(mocks.terminal.reconnect).toHaveBeenCalledTimes(1)
    expect(mocks.vnc.reload).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('reloads the noVNC frame when the desktop tab is active', async () => {
    const wrapper = mountView()
    mocks.tabsState.activeTab = 'desktop'

    await emitAction(wrapper, 'reload')

    expect(mocks.vnc.reload).toHaveBeenCalledTimes(1)
    expect(mocks.terminal.reconnect).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('is a safe no-op when the workspace is not mounted', async () => {
    mocks.session.isActive = false
    const wrapper = mountView()

    await expect(emitAction(wrapper, 'reload')).resolves.toBeUndefined()
    expect(mocks.terminal.reconnect).not.toHaveBeenCalled()
    expect(mocks.vnc.reload).not.toHaveBeenCalled()
    wrapper.unmount()
  })
})
