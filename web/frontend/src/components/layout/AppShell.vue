<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import QuestionDrawer from '@/components/candidate/QuestionDrawer.vue'
import { useTimer } from '@/composables/useTimer'

import AppHeader from './AppHeader.vue'
import type { OverflowAction } from './types'

/**
 * AppShell (FE-020) — the slim candidate shell: a 52px `<AppHeader>` over a
 * full-height workspace slot.
 *
 * The shell owns the FE-023 `useTimer` connection (socket + `/api/timer`
 * fallback + server-clock interpolation) and feeds its formatted value and
 * urgency colour to the header. The header's progress control opens the
 * FE-024 `QuestionDrawer`; task selection is forwarded to the caller.
 *
 * Parity note: the legacy session event bus multiplexes `clipboard_update`,
 * `transition_progress`, `session_expired` and `session_terminated` on the same
 * socket. `useTimer` exposes `handleMessage()` for that multiplexing; wiring the
 * full session event bus is tracked separately (`TODO(integration)`).
 */

const props = withDefaults(
  defineProps<{
    examName?: string | null
    active?: boolean
    currentTask?: number
    totalTasks?: number
    flagged?: boolean
    isAdmin?: boolean
    sessionId?: string | null
    submitting?: boolean
    canViewRecordings?: boolean
    /** Render the FE-024 question navigator (disabled in isolation/tests). */
    showQuestionDrawer?: boolean
  }>(),
  {
    examName: '',
    active: false,
    currentTask: 0,
    totalTasks: 0,
    flagged: false,
    isAdmin: false,
    sessionId: null,
    submitting: false,
    canViewRecordings: false,
    showQuestionDrawer: true,
  },
)

const emit = defineEmits<{
  flag: []
  submit: []
  expired: []
  'copy-session-id': []
  action: [id: OverflowAction]
  'select-task': [taskNum: number]
}>()

const drawerOpen = ref(false)

/**
 * Resolve the session socket URL lazily so it always reflects the current
 * `sessionId` (a plain option string would be captured once at setup).
 */
function sessionSocketUrl(): string {
  const sid = props.sessionId ?? 'active'
  if (typeof window === 'undefined') return `/ws/session/${sid}`
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/session/${sid}`
}

const timer = useTimer({
  url: sessionSocketUrl,
  autoConnect: false,
  onExpired: () => emit('expired'),
})

watch(
  () => props.active,
  (active) => {
    if (active) timer.start()
    else timer.stop()
  },
  { immediate: true },
)

const timerText = computed(() => timer.formatted.value)
const timerUrgency = computed(() => timer.urgency.value)
</script>

<template>
  <div class="flex h-full min-h-0 flex-col bg-app" data-testid="app-shell">
    <AppHeader
      :exam-name="examName"
      :active="active"
      :current-task="currentTask"
      :total-tasks="totalTasks"
      :flagged="flagged"
      :is-admin="isAdmin"
      :session-id="sessionId"
      :timer-text="timerText"
      :timer-urgency="timerUrgency"
      :submitting="submitting"
      :can-view-recordings="canViewRecordings"
      @flag="emit('flag')"
      @submit="emit('submit')"
      @open-questions="drawerOpen = true"
      @copy-session-id="emit('copy-session-id')"
      @action="emit('action', $event)"
    />

    <main class="min-h-0 flex-1 overflow-hidden">
      <slot />
    </main>

    <QuestionDrawer
      v-if="showQuestionDrawer"
      v-model="drawerOpen"
      title="Question navigator"
      @select="emit('select-task', $event)"
    />
  </div>
</template>
