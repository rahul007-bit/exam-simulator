<script setup lang="ts">
import { computed, nextTick, ref, useTemplateRef, watch } from 'vue'

import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import RecordingsModal from '@/components/candidate/RecordingsModal.vue'
import WorkspaceSplit from '@/components/layout/WorkspaceSplit.vue'
import { Badge, Button, Input, Modal } from '@/components/ui'
import NoVncFrame from '@/components/workspace/NoVncFrame.vue'
import XTerm from '@/components/workspace/XTerm.vue'
import { notifySession } from '@/api/admin'
import { useConfirm } from '@/composables/useConfirm'
import { useObserve } from '@/composables/useObserve'
import type { ObserveAction, ObserveActionResult } from '@/composables/useObserve'
import { useToast } from '@/composables/useToast'

/**
 * ObserveOverlay (FE-035) — full-screen, view-only admin "observe" surface.
 *
 * Reuses the imperative islands so the observed session behaves exactly like the
 * candidate workspace, but against the **explicit** `sessionId` passed in:
 *
 *   - Desktop → `NoVncFrame` with `view-only` (append-only VNC; no input).
 *   - Terminal → `XTerm` over `/ws/terminal/<sessionId>`.
 *
 * The overlay never derives a session id from "active"/"default": the islands are
 * only mounted when a concrete id exists, so an admin tab can never attach to a
 * different candidate (server also rejects fuzzed attaches with WS 1008).
 *
 * Admin controls (Reset exam / End & grade) run through `useConfirm` and report
 * via `useToast`; the parent orchestrator is notified through `action` so it can
 * refresh its sessions table. No raw hex, glow or emoji — tokens/Tailwind only.
 */

type ObserveTab = 'desktop' | 'terminal'

interface TerminalHandle {
  fit: () => void
  reconnect: () => void
}

const props = withDefaults(
  defineProps<{
    open: boolean
    /** Explicit session to observe. Never falls back to the active session. */
    sessionId: string
    /** Optional display name for the header. */
    sessionName?: string
  }>(),
  { sessionName: '' },
)

const emit = defineEmits<{
  close: []
  action: [payload: { action: ObserveAction; result: ObserveActionResult }]
}>()

const TABS: ReadonlyArray<{ value: ObserveTab; label: string }> = [
  { value: 'desktop', label: 'Desktop' },
  { value: 'terminal', label: 'Terminal' },
]

const { confirm } = useConfirm()
const { push } = useToast()

const {
  detail,
  loading,
  refreshing,
  error,
  pendingAction,
  ready,
  refresh,
  runAction,
} = useObserve({
  sessionId: () => props.sessionId,
  active: () => props.open,
})

const overlayRef = useTemplateRef<HTMLDivElement>('overlay')
const terminalRef = useTemplateRef<TerminalHandle>('terminal')
const activeTab = ref<ObserveTab>('desktop')
/** Review & replay dialog (legacy `observeReviewAndReplay`). */
const reviewOpen = ref(false)
/** Admin -> candidate desktop notification. */
const notifyOpen = ref(false)
const notifyMessage = ref('')
const notifying = ref(false)

const currentTask = computed(() => detail.value?.current_task ?? null)

const progressLabel = computed(() => {
  const value = detail.value
  if (!value) return 'Waiting for session data'
  if (value.total_tasks <= 0) return 'No tasks in preset'
  const taskNum = currentTask.value?.task_num ?? value.current_index + 1
  return `Task ${taskNum} of ${value.total_tasks}`
})

const containerLabel = computed(() =>
  detail.value?.container_running ? 'Container running' : 'Container stopped',
)

const statusLabel = computed(() => detail.value?.status ?? 'unknown')

const tokenLabel = computed(() => {
  const token = detail.value?.candidate_token
  if (!token) return 'No candidate token'
  return `Token ${token.slice(0, 10)}…`
})

const title = computed(() => {
  if (props.sessionName) return props.sessionName
  if (detail.value?.name) return detail.value.name
  return 'Observed session'
})

function actionLabel(action: ObserveAction): string {
  if (action === 'terminate') return 'Terminate session'
  if (action === 'reset') return 'Reset exam'
  return 'End & grade'
}

function describeError(cause: unknown): string {
  return cause instanceof Error ? cause.message : String(cause)
}

function close(): void {
  emit('close')
}

/** Open the recordings/replay dialog for the observed session (legacy parity). */
function openReview(): void {
  if (!ready.value) return
  reviewOpen.value = true
}

async function sendNotification(): Promise<void> {
  const message = notifyMessage.value.trim()
  if (!message || !ready.value) return
  notifying.value = true
  try {
    await notifySession(props.sessionId, message)
    push({ variant: 'success', message: 'Notification sent to the candidate desktop' })
    notifyOpen.value = false
    notifyMessage.value = ''
  } catch (cause) {
    push({
      variant: 'error',
      title: 'Could not send notification',
      message: describeError(cause),
    })
  } finally {
    notifying.value = false
  }
}

function showTab(tab: ObserveTab): void {
  if (activeTab.value === tab) return
  activeTab.value = tab
  if (tab === 'terminal') {
    void nextTick(() => {
      if (typeof requestAnimationFrame === 'function') {
        requestAnimationFrame(() => terminalRef.value?.fit())
      } else {
        terminalRef.value?.fit()
      }
    })
  }
}

async function perform(action: ObserveAction): Promise<void> {
  try {
    const result = await runAction(action)
    push({
      variant: 'success',
      message: result.message || `${actionLabel(action)} completed`,
    })
    emit('action', { action, result })
    if (action !== 'terminate') void refresh()
  } catch (cause) {
    push({
      variant: 'error',
      title: `Could not ${actionLabel(action).toLowerCase()}`,
      message: describeError(cause),
    })
  }
}

async function onReset(): Promise<void> {
  const approved = await confirm({
    title: 'Reset exam?',
    message:
      'This clears the active exam for this candidate and resets the cluster namespaces. The candidate keeps observing the session.',
    confirmLabel: 'Reset exam',
    danger: true,
  })
  if (!approved) return
  await perform('reset')
}

async function onEnd(): Promise<void> {
  const approved = await confirm({
    title: 'End & grade?',
    message:
      'This submits and evaluates the candidate tasks now, then archives the session.',
    confirmLabel: 'End & grade',
    danger: true,
  })
  if (!approved) return
  await perform('end')
}

watch(
  () => props.open,
  (open) => {
    if (!open) {
      reviewOpen.value = false
      return
    }
    activeTab.value = 'desktop'
    void nextTick(() => overlayRef.value?.focus())
  },
)
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      ref="overlay"
      class="fixed inset-0 z-[900] flex flex-col bg-app text-text outline-none"
      role="dialog"
      aria-modal="true"
      :aria-label="`Observing session ${sessionId}`"
      tabindex="-1"
      data-testid="observe-overlay"
      @keydown.escape="close"
    >
      <header
        class="flex flex-none flex-wrap items-center gap-x-4 gap-y-2 border-b border-border bg-surface px-4 py-2.5"
      >
        <div class="flex min-w-0 flex-col">
          <div class="flex items-center gap-2">
            <span class="text-sm font-semibold text-text">Observe</span>
            <span
              class="truncate rounded-[var(--radius-sm)] border border-border bg-app px-1.5 py-0.5 font-mono text-xs text-text-muted"
              data-testid="observe-session-id"
            >
              #{{ sessionId || 'none' }}
            </span>
          </div>
          <span class="truncate text-xs text-text-muted">{{ title }}</span>
        </div>

        <div class="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-muted">
          <span data-testid="observe-status">Status: {{ statusLabel }}</span>
          <span aria-hidden="true">·</span>
          <span data-testid="observe-progress">{{ progressLabel }}</span>
          <span aria-hidden="true">·</span>
          <span data-testid="observe-container">{{ containerLabel }}</span>
          <span aria-hidden="true">·</span>
          <span class="font-mono" data-testid="observe-token">{{ tokenLabel }}</span>
        </div>

        <div class="ml-auto flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            :loading="refreshing"
            :disabled="!ready"
            data-testid="observe-refresh"
            @click="refresh"
          >
            Refresh
          </Button>
          <Button
            variant="secondary"
            size="sm"
            :disabled="!ready"
            data-testid="observe-review"
            @click="openReview"
          >
            Review &amp; replay
          </Button>
          <Button
            variant="secondary"
            size="sm"
            :disabled="!ready"
            data-testid="observe-notify"
            @click="notifyOpen = true"
          >
            Notify
          </Button>
          <Button
            variant="secondary"
            size="sm"
            :disabled="!ready || pendingAction !== null"
            :loading="pendingAction === 'reset'"
            data-testid="observe-reset"
            @click="onReset"
          >
            Reset exam
          </Button>
          <Button
            variant="primary"
            size="sm"
            :disabled="!ready || pendingAction !== null"
            :loading="pendingAction === 'end'"
            data-testid="observe-end"
            @click="onEnd"
          >
            End &amp; grade
          </Button>
          <Button
            variant="ghost"
            size="sm"
            data-testid="observe-close"
            @click="close"
          >
            Close
          </Button>
        </div>
      </header>

      <div
        v-if="error"
        class="flex-none border-b border-border bg-danger/10 px-4 py-1.5 text-xs text-danger-text"
        role="alert"
        data-testid="observe-error"
      >
        {{ error }}
      </div>

      <div
        v-if="!ready"
        class="flex flex-1 items-center justify-center p-6 text-sm text-text-muted"
        data-testid="observe-empty"
      >
        No explicit session selected — observation is disabled to prevent attaching to a
        different candidate.
      </div>

      <template v-else>
        <div class="min-h-0 flex-1">
          <WorkspaceSplit
            storage-key="cka:observe:split"
            :default-ratio="28"
            :min-left="280"
            :min-right="480"
          >
            <!-- Left: candidate task instructions + full task list (legacy
                 `refreshObserveData`). -->
            <template #left>
              <aside
                class="flex h-full w-full flex-col bg-surface"
                data-testid="observe-task-pane"
              >
                <div
                  class="flex flex-none items-center justify-between gap-2 border-b border-border px-4 py-2"
                >
                  <span class="text-sm font-semibold text-text">Task instructions</span>
                  <span
                    class="rounded-[var(--radius-sm)] border border-border bg-app px-1.5 py-0.5 font-mono text-xs text-text-muted"
                    data-testid="observe-task-progress"
                  >
                    {{ progressLabel }}
                  </span>
                </div>

                <div
                  class="min-h-0 flex-1 overflow-y-auto p-4"
                  data-testid="observe-task-instructions"
                >
                  <template v-if="currentTask">
                    <div class="mb-3 flex flex-wrap gap-2">
                      <Badge variant="accent">{{ currentTask.points }} pts</Badge>
                      <Badge variant="neutral">
                        context: {{ currentTask.target_context || 'k3d-cka' }}
                      </Badge>
                      <Badge variant="neutral">
                        ns: {{ currentTask.namespace || 'default' }}
                      </Badge>
                      <Badge v-if="currentTask.is_flagged" variant="warning">Flagged</Badge>
                    </div>
                    <h2 class="mb-3 text-base font-semibold text-text">{{ currentTask.title }}</h2>
                    <MarkdownRenderer :source="currentTask.description" />
                  </template>
                  <p v-else class="text-sm text-text-muted">
                    {{ loading ? 'Loading candidate task…' : 'No current task to display.' }}
                  </p>

                  <div
                    v-if="detail?.questions?.length"
                    class="mt-6 border-t border-border pt-4"
                  >
                    <h3 class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">
                      All tasks in exam
                    </h3>
                    <ul
                      class="m-0 flex list-none flex-col gap-1 p-0"
                      data-testid="observe-task-list"
                    >
                      <li
                        v-for="question in detail.questions"
                        :key="question.id"
                        :class="[
                          'flex items-center justify-between gap-2 rounded-[var(--radius-sm)] border px-2 py-1.5 text-xs',
                          question.is_current
                            ? 'border-accent bg-[var(--color-accent-subtle)] text-text'
                            : 'border-transparent bg-elevated text-text-muted',
                        ]"
                        :aria-current="question.is_current ? 'true' : undefined"
                        data-testid="observe-task-item"
                      >
                        <span class="min-w-0 truncate">
                          <span class="font-mono text-text-dim">#{{ question.task_num }}</span>
                          <span class="ml-1 font-medium">{{ question.title }}</span>
                        </span>
                        <span class="flex flex-none items-center gap-1.5">
                          <span
                            v-if="question.is_flagged"
                            class="font-semibold text-warning-text"
                          >
                            FLAG
                          </span>
                          <span class="tabular-nums">{{ question.points }} pts</span>
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>
              </aside>
            </template>

            <!-- Right: view-only desktop / admin terminal. -->
            <div class="flex h-full min-h-0 flex-col">
              <div
                class="flex flex-none items-center gap-3 border-b border-border bg-app px-4 py-2"
              >
                <div
                  class="inline-flex items-center gap-0.5 rounded-[var(--radius-md)] border border-border bg-surface p-0.5"
                  role="tablist"
                  aria-label="Observe view"
                >
                  <button
                    v-for="tab in TABS"
                    :key="tab.value"
                    type="button"
                    role="tab"
                    :aria-selected="activeTab === tab.value"
                    :class="[
                      'inline-flex h-7 items-center rounded-[var(--radius-sm)] px-3 text-xs font-medium transition-colors',
                      activeTab === tab.value
                        ? 'bg-accent-solid text-accent-contrast'
                        : 'text-text-muted hover:bg-hover hover:text-text',
                      'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus-ring-color)]',
                    ]"
                    :data-testid="`observe-tab-${tab.value}`"
                    @click="showTab(tab.value)"
                  >
                    {{ tab.label }}
                  </button>
                </div>

                <span class="min-w-0 truncate text-xs text-text-muted">
                  {{
                    activeTab === 'desktop'
                      ? 'Desktop input is blocked for view-only observation.'
                      : 'Terminal runs an admin shell against the candidate container.'
                  }}
                </span>
              </div>

              <div class="relative min-h-0 flex-1 p-2">
                <div v-show="activeTab === 'desktop'" class="absolute inset-2">
                  <NoVncFrame
                    :session-id="sessionId"
                    :active="open && activeTab === 'desktop'"
                    view-only
                    title="Observed desktop"
                    aria-label="Observed remote desktop (view only)"
                  />
                </div>
                <div v-show="activeTab === 'terminal'" class="absolute inset-2">
                  <XTerm
                    ref="terminal"
                    :session-id="sessionId"
                    auto-connect
                    aria-label="Observed session terminal"
                  />
                </div>
              </div>
            </div>
          </WorkspaceSplit>
        </div>
      </template>

      <Teleport to="body">
        <RecordingsModal
          v-model="reviewOpen"
          :initial-session-id="sessionId"
          :show-list="false"
        />
      </Teleport>

      <Modal v-model="notifyOpen" title="Notify candidate" size="sm" data-testid="observe-notify-modal">
        <Input
          v-model="notifyMessage"
          label="Message"
          placeholder="e.g. 10 minutes remaining"
          data-testid="observe-notify-message"
        />
        <template #footer>
          <Button variant="secondary" @click="notifyOpen = false">Cancel</Button>
          <Button
            variant="primary"
            :loading="notifying"
            :disabled="!notifyMessage.trim()"
            data-testid="observe-notify-send"
            @click="sendNotification"
          >
            Send
          </Button>
        </template>
      </Modal>
    </div>
  </Teleport>
</template>
