<script setup lang="ts">
import { computed } from 'vue'

import Icon from '@/components/Icon.vue'
import ThemeToggle from '@/components/ThemeToggle.vue'
import { Button } from '@/components/ui'
import type { TimerUrgency } from '@/stores/timer'

import OverflowMenu from './OverflowMenu.vue'
import { buildOverflowMenu, progressLabel } from './menu'
import type { HeaderMenuItem, OverflowAction } from './types'

/**
 * AppHeader (FE-020) — the slim 52px candidate header.
 *
 * Primary controls only: exam name (truncated) · progress · session-id copy ·
 * timer · Flag · Submit · `⋯` overflow. Everything secondary (Fullscreen,
 * Reload, New tab, Copy from Desktop, Recordings, admin End/Reset) lives in the
 * single overflow menu so the bar never wraps or clips at 1366×768 or
 * 1920×1080. The timer is colour-only (FE-023 urgency) with no pulse/glow.
 */

const props = withDefaults(
  defineProps<{
    examName?: string | null
    /** An exam is running; Flag/Submit/progress are shown. */
    active?: boolean
    currentTask?: number
    totalTasks?: number
    flagged?: boolean
    isAdmin?: boolean
    sessionId?: string | null
    /** Preformatted timer (FE-023); defaults to `--:--`. */
    timerText?: string
    timerUrgency?: TimerUrgency
    /** Disables the primary actions while a request is in flight. */
    submitting?: boolean
    /** Recordings entry visibility (legacy gates this to admins). */
    canViewRecordings?: boolean
  }>(),
  {
    examName: '',
    active: false,
    currentTask: 0,
    totalTasks: 0,
    flagged: false,
    isAdmin: false,
    sessionId: null,
    timerText: '--:--',
    timerUrgency: 'normal',
    submitting: false,
    canViewRecordings: false,
  },
)

const emit = defineEmits<{
  flag: []
  submit: []
  'open-questions': []
  'copy-session-id': []
  action: [id: OverflowAction]
}>()

const menuItems = computed<HeaderMenuItem[]>(() =>
  buildOverflowMenu({
    hasSessionId: Boolean(props.sessionId),
    isAdmin: props.isAdmin,
    canViewRecordings: props.canViewRecordings,
  }),
)

const displayName = computed(() => props.examName?.trim() || 'Kubernetes Exam Simulator')
const progress = computed(() =>
  progressLabel({ current: props.currentTask, total: props.totalTasks }),
)

const TIMER_TONES: Record<TimerUrgency, string> = {
  normal: 'text-text',
  warning: 'text-warning-text',
  critical: 'text-danger-text',
}
const timerTone = computed(() => TIMER_TONES[props.timerUrgency])

function onMenuSelect(id: string): void {
  emit('action', id as OverflowAction)
}
</script>

<template>
  <header
    class="flex h-[var(--header-height)] flex-none items-center gap-2 border-b border-border bg-surface px-3 sm:gap-3 sm:px-4"
    data-testid="candidate-header"
  >
    <!-- Exam name (truncates so controls never get pushed off-screen) -->
    <div class="flex min-w-0 flex-1 items-center">
      <span
        class="min-w-0 truncate text-sm font-semibold text-text"
        :title="displayName"
        aria-label="Exam"
        data-testid="header-exam-name"
      >
        {{ displayName }}
      </span>
    </div>

    <!-- Progress + timer -->
    <div class="flex flex-none items-center gap-2 sm:gap-3">
      <Button
        v-if="active && totalTasks > 0"
        variant="secondary"
        size="sm"
        :aria-label="`Open question navigator. ${progress}`"
        :title="progress"
        data-testid="header-progress"
        @click="emit('open-questions')"
      >
        <Icon name="menu" :size="16" />
        <span class="tabular-nums">{{ progress }}</span>
      </Button>

      <button
        v-if="sessionId"
        type="button"
        class="flex max-w-[12rem] items-center gap-1.5 rounded-[var(--radius-sm)] border border-border bg-elevated px-2 py-1 text-xs text-text-muted transition-colors hover:bg-hover hover:text-text"
        :title="`Copy session ID ${sessionId}`"
        :aria-label="`Copy session ID ${sessionId}`"
        data-testid="header-session-id"
        @click="emit('copy-session-id')"
      >
        <Icon name="copy" :size="14" class="flex-none" />
        <span class="truncate font-mono">#{{ sessionId }}</span>
      </button>

      <div
        class="flex items-center gap-1.5 rounded-[var(--radius-sm)] border border-border bg-elevated px-2 py-1"
        :class="timerTone"
        data-testid="header-timer"
      >
        <Icon name="clock" :size="16" />
        <span class="font-mono text-sm tabular-nums">{{ timerText }}</span>
      </div>
    </div>

    <!-- Primary actions + overflow -->
    <div class="flex flex-none items-center gap-1.5 sm:gap-2">
      <Button
        v-if="active"
        size="sm"
        :variant="flagged ? 'warning' : 'secondary'"
        :aria-pressed="flagged"
        :disabled="submitting"
        data-testid="header-flag"
        @click="emit('flag')"
      >
        <Icon name="flag" :size="14" />
        <span>{{ flagged ? 'Flagged' : 'Flag' }}</span>
      </Button>

      <Button
        v-if="active"
        size="sm"
        variant="danger"
        :loading="submitting"
        data-testid="header-submit"
        @click="emit('submit')"
      >
        Submit exam
      </Button>

      <ThemeToggle />

      <OverflowMenu :items="menuItems" :disabled="submitting" @select="onMenuSelect" />
    </div>
  </header>
</template>
