<script setup lang="ts">
import { RadioGroup, RadioGroupLabel, RadioGroupOption } from '@headlessui/vue'
import { nextTick, ref, useTemplateRef } from 'vue'

import Icon from '@/components/Icon.vue'
import NoVncFrame from '@/components/workspace/NoVncFrame.vue'
import XTerm from '@/components/workspace/XTerm.vue'
import { FOCUS_RING } from '@/components/ui'
import type { IconName } from '@/components/ui'

/**
 * WorkspaceTabs (FE-026) — the 36px segmented Desktop/Terminal control and the
 * viewport that hosts the two imperative islands.
 *
 * Behaviour preserved from the legacy `switchWorkspaceTab` (`app.js:1624`):
 * both frames stay mounted and only visibility toggles, so the noVNC session and
 * the terminal socket survive a round-trip switch. Colours come from FE-012
 * tokens only — no raw hex, glow or emoji.
 */

type WorkspaceTab = 'desktop' | 'terminal'

interface TerminalHandle {
  fit: () => void
  reconnect: () => void
  connect: () => void
  disconnect: () => void
}

interface VncHandle {
  reload: () => void
  sendClipboard: (text: string) => boolean
  frame: HTMLIFrameElement | null
}

const props = withDefaults(
  defineProps<{
    sessionId: string
    defaultTab?: WorkspaceTab
    viewOnly?: boolean
    autoConnectTerminal?: boolean
  }>(),
  { defaultTab: 'desktop', viewOnly: false, autoConnectTerminal: true },
)

const emit = defineEmits<{ 'update:tab': [tab: WorkspaceTab] }>()

const TABS: ReadonlyArray<{ value: WorkspaceTab; label: string; icon: IconName }> = [
  { value: 'desktop', label: 'Desktop', icon: 'desktop' },
  { value: 'terminal', label: 'Terminal', icon: 'terminal' },
]

const activeTab = ref<WorkspaceTab>(props.defaultTab)
const terminalRef = useTemplateRef<TerminalHandle>('terminal')
const vncRef = useTemplateRef<VncHandle>('desktop')

function showTab(tab: WorkspaceTab): void {
  if (activeTab.value === tab) return
  activeTab.value = tab
  emit('update:tab', tab)

  if (tab === 'terminal') {
    // The island was hidden (display:none); refit once it is laid out.
    void nextTick(() => {
      if (typeof requestAnimationFrame === 'function') {
        requestAnimationFrame(() => terminalRef.value?.fit())
      } else {
        terminalRef.value?.fit()
      }
    })
  }
}

function handleUpdate(value: string): void {
  showTab(value as WorkspaceTab)
}

defineExpose({
  activeTab,
  showTab,
  terminal: terminalRef,
  vnc: vncRef,
})
</script>

<template>
  <section class="flex h-full min-h-0 flex-col bg-app text-text" data-testid="workspace-tabs">
    <div class="flex h-9 flex-none items-center border-b border-border bg-surface px-2">
      <RadioGroup
        :model-value="activeTab"
        class="h-full"
        data-testid="workspace-tab-control"
        @update:model-value="handleUpdate"
      >
        <RadioGroupLabel class="sr-only">Workspace view</RadioGroupLabel>
        <div
          class="inline-flex h-full items-center gap-0.5 rounded-[var(--radius-md)] border border-border bg-app p-0.5"
        >
          <RadioGroupOption
            v-for="tab in TABS"
            :key="tab.value"
            v-slot="{ checked }"
            as="template"
            :value="tab.value"
          >
            <button
              type="button"
              :class="[
                'inline-flex h-full items-center gap-1.5 rounded-[var(--radius-sm)] px-3 text-xs font-medium transition-colors',
                checked
                  ? 'bg-accent-solid text-accent-contrast'
                  : 'text-text-muted hover:bg-hover hover:text-text',
                FOCUS_RING,
              ]"
              :data-testid="`workspace-tab-${tab.value}`"
            >
              <Icon :name="tab.icon" :size="14" />
              <span>{{ tab.label }}</span>
            </button>
          </RadioGroupOption>
        </div>
      </RadioGroup>
    </div>

    <div class="relative min-h-0 flex-1">
      <div v-show="activeTab === 'desktop'" class="absolute inset-0">
        <NoVncFrame
          ref="desktop"
          :session-id="sessionId"
          :active="activeTab === 'desktop'"
          :view-only="viewOnly"
        />
      </div>
      <div v-show="activeTab === 'terminal'" class="absolute inset-0">
        <XTerm
          ref="terminal"
          :session-id="sessionId"
          :auto-connect="autoConnectTerminal"
          aria-label="Terminal"
        />
      </div>
    </div>
  </section>
</template>
