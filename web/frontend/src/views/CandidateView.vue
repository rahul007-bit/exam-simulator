<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { SubmitResponse } from '@/api/actions'
import { persistCandidateToken, readCandidateToken } from '@/api/session'
import ExamScorecard from '@/components/candidate/ExamScorecard.vue'
import RecordingsModal from '@/components/candidate/RecordingsModal.vue'
import TaskPane from '@/components/candidate/TaskPane.vue'
import FullscreenGuard from '@/components/FullscreenGuard.vue'
import AppShell from '@/components/layout/AppShell.vue'
import WorkspaceSplit from '@/components/layout/WorkspaceSplit.vue'
import type { OverflowAction } from '@/components/layout/types'
import { Button, Card, Modal, Spinner } from '@/components/ui'
import ClipboardBridge from '@/components/workspace/ClipboardBridge.vue'
import WorkspaceTabs from '@/components/workspace/WorkspaceTabs.vue'
import { useConfirm } from '@/composables/useConfirm'
import { useFullscreen } from '@/composables/useFullscreen'
import { useToast } from '@/composables/useToast'
import { useSessionStore } from '@/stores/session'
import { useAuthStore } from '@/stores/auth'
import { useTimerStore } from '@/stores/timer'

/**
 * CandidateView (FE-020/FE-021) — the `/` route, rendered inside the slim
 * `AppShell`.
 *
 * FE-020 owns the shell + header; FE-021 owns the workspace split (left task
 * pane / right desktop+terminal pane, persisted ratio, collapse toggle). The
 * terminal and desktop islands (FE-025/FE-026), clipboard (FE-027), fullscreen
 * (FE-028) and recordings (FE-029) are wired by their own tasks; FE-026 mounts
 * its tab bar in the marked `TODO(workspace-tabs)` slot. Remaining integration
 * points are marked `TODO(integration)`, including the overflow-menu routing.
 */

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const auth = useAuthStore()
const timer = useTimerStore()
const { push } = useToast()
const { confirm } = useConfirm()

const scorecard = ref<SubmitResponse | null>(null)
const scorecardOpen = ref(false)
const recordingsOpen = ref(false)

const token = computed(() => (typeof route.query.token === 'string' ? route.query.token : undefined))

// FS-008: `/` is not a public landing page. Until the auth session (and any
// resumable session) is resolved we render a spinner, then either continue or
// redirect to /login.
const authReady = ref(false)

const active = computed(() => session.isActive)
const sessionId = computed(() => session.sessionId)
const examName = computed(() => {
  const data = session.data
  if (data && data.active === true) return data.name
  return session.lockedPreset?.name ?? 'Kubernetes Exam Simulator'
})
const currentTask = computed(() => session.currentTaskNum)
const totalTasks = computed(() => session.totalTasks)
const currentTaskModel = computed(() => session.currentTask)
const flagged = computed(() => {
  const task = session.currentTask
  return task ? session.flaggedIds.includes(task.id) : false
})
const submitting = computed(() => session.loading)

// Fullscreen anti-cheat (FE-028) + clipboard bridge (FE-027).
const fullscreen = useFullscreen({
  isAdmin: computed(() => session.isAdmin),
  isActive: active,
})
const clipboardBridge = ref<InstanceType<typeof ClipboardBridge> | null>(null)
const workspaceTabs = ref<InstanceType<typeof WorkspaceTabs> | null>(null)

// Keep the FE-023 timer store in sync whenever a session payload is applied.
watch(
  () => session.data,
  (data) => {
    if (data) timer.syncFromSession(data)
  },
)

onMounted(async () => {
  // FS-008: `/` is not a public landing page. Resolve auth and any resumable
  // session first; without an invitation, a live session or a sign-in, redirect
  // to the login page (invitation links and signed-in users continue normally).
  if (!auth.initialized) await auth.check()

  const queryToken = token.value
  if (queryToken) {
    persistCandidateToken(queryToken)
    await session.fetchSession({ token: queryToken })
  } else {
    const resumeToken = readCandidateToken()
    if (resumeToken) await session.fetchSession({ token: resumeToken })
  }

  if (!auth.isAuthenticated && !token.value && !session.isActive) {
    void router.replace({ name: 'login', query: { redirect: route.fullPath } })
    return
  }

  authReady.value = true
})

async function onFlag(): Promise<void> {
  await session.flag()
  if (session.error) push({ variant: 'error', message: session.error })
}

async function onSubmit(): Promise<void> {
  const ok = await confirm({
    title: 'Submit exam',
    message: 'Submit your exam for evaluation? This finalizes your score across all questions.',
    confirmLabel: 'Submit exam',
    danger: true,
  })
  if (!ok) return

  const result = await session.submit()
  if (result) {
    scorecard.value = result
    scorecardOpen.value = true
    push({ variant: 'success', message: 'Exam submitted' })
  } else if (session.error) {
    push({ variant: 'error', message: session.error })
  }
}

async function onSelectTask(taskNum: number): Promise<void> {
  const response = await session.jump(taskNum)
  if (!response && session.error) push({ variant: 'error', message: session.error })
}

async function onPrev(): Promise<void> {
  const response = await session.prev()
  if (!response && session.error) push({ variant: 'error', message: session.error })
}

async function onNext(): Promise<void> {
  const response = await session.next()
  if (!response && session.error) push({ variant: 'error', message: session.error })
}

async function onResetTask(): Promise<void> {
  const ok = await confirm({
    title: 'Reset task',
    message:
      'Reset this task back to its initial problem state? Any changes made to this task will be reset.',
    confirmLabel: 'Reset task',
    danger: true,
  })
  if (!ok) return

  const reset = await session.retry()
  if (reset) {
    push({ variant: 'success', message: 'Task reset' })
  } else if (session.error) {
    push({ variant: 'error', message: session.error })
  }
}

async function onStart(): Promise<void> {
  fullscreen.enter()
  if (token.value) persistCandidateToken(token.value)
  const response = await session.start({
    candidate_token: token.value,
  })
  if (!response && session.error) push({ variant: 'error', message: session.error })
}

/**
 * Owner-lock retry: re-fetch the session (preferring the candidate token) after
 * the other window/device releases the lock. A locked session is not an error,
 * so the retry simply reloads the state.
 */
async function onRetryLocked(): Promise<void> {
  const resumeToken = token.value ?? readCandidateToken() ?? undefined
  await session.fetchSession(resumeToken ? { token: resumeToken } : undefined)
  if (session.error) push({ variant: 'error', message: session.error })
}

async function onCopySessionId(): Promise<void> {
  const sid = sessionId.value
  if (!sid) return
  try {
    await navigator.clipboard.writeText(sid)
    push({ variant: 'success', message: `Copied session ID #${sid}` })
  } catch {
    push({ variant: 'error', message: 'Could not copy session ID' })
  }
}

/**
 * A code copy inside the task pane also mirrors the text into the noVNC desktop
 * clipboard (legacy `copyCode`/`copyInlineCode` → `syncTextToVnc`). Plain
 * selection copies are handled by the `document` `copy` listener in
 * `ClipboardBridge`.
 */
function onTaskCopy(text: string): void {
  if (!text) return
  clipboardBridge.value?.sendToVnc(text)
}

async function onAction(id: OverflowAction): Promise<void> {
  switch (id) {
    case 'copy-session-id':
      await onCopySessionId()
      return
    case 'admin-end':
      await onSubmit()
      return
    case 'admin-reset': {
      const ok = await confirm({
        title: 'Reset exam',
        message: 'Clear the current session and return to the start screen?',
        confirmLabel: 'Reset exam',
        danger: true,
      })
      if (!ok) return
      const reset = await session.reset()
      if (reset) {
        scorecard.value = null
        push({ variant: 'success', message: 'Session reset' })
      } else if (session.error) {
        push({ variant: 'error', message: session.error })
      }
      return
    }
    case 'fullscreen':
      await fullscreen.toggle()
      return
    case 'copy-from-desktop':
      clipboardBridge.value?.copyFromDesktopToHost()
      return
    case 'recordings':
      recordingsOpen.value = true
      return
    // TODO(integration): route once FE-026 new-tab lands:
    //   new-tab -> new workspace tab
    case 'reload': {
      // Legacy `reloadWorkspaceFrame` parity: reconnect the terminal when it is
      // active, otherwise force a fresh noVNC connection by reloading the frame.
      const tabs = workspaceTabs.value
      if (!tabs) return
      if (tabs.activeTab === 'terminal') {
        tabs.terminal?.reconnect()
      } else {
        tabs.vnc?.reload()
      }
      return
    }
    case 'new-tab':
    default:
      return
  }
}
</script>

<template>
  <AppShell
    :exam-name="examName"
    :active="active"
    :current-task="currentTask"
    :total-tasks="totalTasks"
    :flagged="flagged"
    :is-admin="session.isAdmin"
    :session-id="sessionId"
    :submitting="submitting"
    :can-view-recordings="session.isAdmin"
    @flag="onFlag"
    @submit="onSubmit"
    @action="onAction"
    @copy-session-id="onCopySessionId"
    @select-task="onSelectTask"
  >
    <div class="h-full min-h-0">
      <div v-if="active" class="h-full min-h-0" data-testid="candidate-workspace">
        <WorkspaceSplit>
          <!-- Left pane: FE-022 task pane -->
          <template #left>
            <TaskPane
              :task="currentTaskModel"
              :task-num="currentTask"
              :total-tasks="totalTasks"
              :busy="session.loading"
              @copy="onTaskCopy"
              @prev="onPrev"
              @next="onNext"
              @reset="onResetTask"
            />
          </template>

          <!-- Right pane (workspace majority): FE-026 Desktop/Terminal workspace
               hosting the noVNC and XTerm islands (both stay mounted). -->
          <WorkspaceTabs ref="workspaceTabs" :session-id="sessionId ?? 'active'" />
        </WorkspaceSplit>
      </div>

      <div
        v-else-if="session.isLocked"
        class="flex h-full items-center justify-center p-6"
        data-testid="session-locked"
      >
        <Card
          title="This exam is already in progress"
          subtitle="Active in another window or device"
          variant="elevated"
          class="w-full max-w-lg"
        >
          <div class="flex flex-col gap-4">
            <p class="m-0 text-sm text-text-muted">
              This exam session is active in another window or device. Only one window can work on
              the exam at a time to protect your progress. Close the other window, or continue
              there, then retry.
            </p>
            <div>
              <Button
                variant="primary"
                :loading="session.loading"
                :disabled="session.loading"
                data-testid="session-locked-retry"
                @click="onRetryLocked"
              >
                Retry
              </Button>
            </div>
          </div>
        </Card>
      </div>

      <div
        v-else-if="!authReady"
        class="flex h-full items-center justify-center p-6"
        role="status"
        data-testid="candidate-resolving"
      >
        <Spinner decorative />
      </div>

      <div v-else class="flex h-full items-center justify-center p-6">
        <Card
          title="Kubernetes Exam Simulator"
          subtitle="Select or start an exam to begin."
          class="w-full max-w-lg"
        >
          <div class="flex flex-col gap-4">
            <div>
              <p class="m-0 text-sm font-medium text-text">{{ examName }}</p>
              <p class="m-0 mt-1 text-sm text-text-muted">
                {{
                  session.isInvited
                    ? 'You have an assigned exam.'
                    : 'Start the assigned exam to begin.'
                }}
              </p>
            </div>
            <div class="flex flex-wrap gap-2">
              <Button
                variant="primary"
                :loading="session.loading"
                :disabled="session.loading"
                data-testid="start-exam"
                @click="onStart"
              >
                Start exam
              </Button>
              <Button
                variant="secondary"
                data-testid="go-assignments"
                @click="router.push('/assignments')"
              >
                My assignments
              </Button>
            </div>

            <p
              v-if="session.loading"
              class="m-0 flex items-center gap-2 text-sm text-text-muted"
              role="status"
              data-testid="start-progress"
            >
              <Spinner size="sm" decorative />
              Starting exam — deploying your environment. This can take a minute…
            </p>
          </div>
        </Card>
      </div>
    </div>
  </AppShell>

  <Modal v-model="scorecardOpen" title="Exam results" size="lg">
    <ExamScorecard :result="scorecard" />
    <template #footer>
      <Button variant="secondary" @click="scorecardOpen = false">Close</Button>
    </template>
  </Modal>

  <ClipboardBridge ref="clipboardBridge" :session-id="sessionId" :active="active" />
  <RecordingsModal v-model="recordingsOpen" />
  <FullscreenGuard />
</template>
