<script setup lang="ts">
import { FitAddon } from '@xterm/addon-fit'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/vue'
import { Terminal } from '@xterm/xterm'
import type { ITheme } from '@xterm/xterm'
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  shallowRef,
  useId,
  useTemplateRef,
  watch,
} from 'vue'

import type { RecordingEvent, TaskTimelineEntry } from '@/api/recordings'
import { getRecordingCast } from '@/api/recordings'
import { formatReplayTime, useReplay } from '@/composables/useReplay'
import { Badge, Button, FOCUS_RING, Icon, SegmentedControl, Select, Spinner } from '@/components/ui'
import type { BadgeVariant, SegmentOption, SelectOption } from '@/components/ui'

import '@xterm/xterm/css/xterm.css'

/**
 * ReplayPlayer (FE-029) — imperative asciinema replay island.
 *
 * Renders the `.cast` recording into an xterm.js terminal and drives it with
 * `useReplay` (parser + rAF playback loop ported from the legacy replay engine).
 * The left sidebar owns the actor/channel selector (User ▾ Web/Desktop, Admin)
 * aligned with the Events/Tasks tabs; its event log is filtered by the active
 * channel and synced to the playhead. The right side shows the terminal replay
 * with its transport controls.
 *
 * Parity notes: only `"o"` frames are written, `reset()` + re-feed on seek,
 * `mm:ss` times, and a 0.5–10x speed range — matching the legacy replay engine.
 */

defineOptions({ name: 'ReplayPlayer' })

const props = withDefaults(
  defineProps<{
    /** Raw asciinema v2 `.cast` text. Used when no `sessionId` is supplied. */
    castText?: string | null
    /** Session to replay; when set the `.cast` is fetched per `channel`. */
    sessionId?: string
    /** Active channel: `user-web`, `user-desktop` or `admin-web`. */
    channel?: string
    /** Whether the active channel has a cast (drives the terminal empty state). */
    hasCast?: boolean
    /** Structured session events (used by the event timeline). */
    events?: RecordingEvent[]
    /** Task navigation intervals (used by the tasks timeline). */
    tasks?: TaskTimelineEntry[]
    /** Duration to show when the cast carries no timing (seconds). */
    durationFallback?: number
    ariaLabel?: string
    /** Render the events/tasks sidebar. Default `true`. */
    showTimeline?: boolean
    /** Show the raw Events tab. When `false` only the clickable Tasks list is shown. */
    showEvents?: boolean
  }>(),
  {
    castText: null,
    sessionId: '',
    channel: 'user-web',
    hasCast: true,
    events: () => [],
    tasks: () => [],
    durationFallback: 0,
    ariaLabel: 'Session replay',
    showTimeline: true,
    showEvents: true,
  },
)

const emit = defineEmits<{ 'update:channel': [value: string] }>()

const uid = useId()
const userTabId = computed(() => `replay-tab-user-${uid}`)
const adminTabId = computed(() => `replay-tab-admin-${uid}`)
const panelId = computed(() => `replay-panel-${uid}`)

/** Channels offered by the User ▾ menu — always both, independent of `has_cast`. */
const USER_CHANNELS: SelectOption[] = [
  { value: 'user-web', label: 'Web' },
  { value: 'user-desktop', label: 'Desktop' },
]

const channelModel = computed({
  get: () => props.channel,
  set: (value: string) => emit('update:channel', value),
})
const isAdmin = computed(() => props.channel === 'admin-web')

/** Legacy events predate channel tagging and belong to the candidate web stream. */
const LEGACY_EVENT_CHANNEL = 'user-web'

function eventChannel(event: RecordingEvent): string {
  return event.channel && event.channel.length > 0 ? event.channel : LEGACY_EVENT_CHANNEL
}

/** Events whose channel matches the active actor/channel selection. */
const filteredEvents = computed(() =>
  props.events.filter((event) => eventChannel(event) === props.channel),
)

function actorTabClass(active: boolean): string[] {
  return [
    'inline-flex h-7 items-center justify-center gap-1 rounded-[var(--radius-sm)] px-3 text-xs font-medium transition-colors',
    FOCUS_RING,
    active
      ? 'bg-accent-solid text-accent-contrast'
      : 'text-text-muted hover:bg-hover hover:text-text',
  ]
}

const containerRef = useTemplateRef<HTMLDivElement>('container')
const terminalRef = shallowRef<Terminal | null>(null)
const fitAddonRef = shallowRef<FitAddon | null>(null)

let resizeObserver: ResizeObserver | null = null
let connectFrame: number | null = null
let castController: AbortController | null = null
let castToken = 0
const castLoading = ref(false)

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

const replay = useReplay({
  terminal: terminalRef,
  durationFallback: () => props.durationFallback,
})

const { currentTime, duration, isPlaying, speed, activeEventIndex } = replay

const activeTab = ref<string>(props.showEvents ? 'timeline' : 'tasks')
const ALL_TABS: SegmentOption[] = [
  { value: 'timeline', label: 'Events' },
  { value: 'tasks', label: 'Tasks' },
]
const tabOptions = computed<SegmentOption[]>(() =>
  props.showEvents ? ALL_TABS : ALL_TABS.filter((tab) => tab.value === 'tasks'),
)

const SPEED_OPTIONS: SelectOption[] = [
  { value: '0.5', label: '0.5x' },
  { value: '1', label: '1x' },
  { value: '1.5', label: '1.5x' },
  { value: '2', label: '2x' },
  { value: '4', label: '4x' },
  { value: '8', label: '8x' },
]

const speedModel = computed({
  get: () => String(speed.value),
  set: (value: string) => replay.setSpeed(Number(value)),
})

const hasFrames = computed(() => replay.frames.value.length > 0)

const activeTaskIndex = computed(() => {
  let active = -1
  props.tasks.forEach((task, index) => {
    if (Number(task.first_seen_time ?? 0) <= currentTime.value) active = index
  })
  return active
})

function eventTime(event: RecordingEvent): number {
  return Number(event.rel_time ?? 0)
}

function taskTime(task: TaskTimelineEntry): number {
  return Number(task.first_seen_time ?? 0)
}

function str(value: unknown): string {
  return typeof value === 'string' ? value : value == null ? '' : String(value)
}

function eventVariant(type: string): BadgeVariant {
  if (type === 'SESSION_START' || type === 'EXAM_SUBMITTED') return 'success'
  if (type === 'TASK_FLAGGED' || type === 'TASK_UNFLAGGED' || type === 'TASK_RETRY')
    return 'warning'
  if (type === 'TASK_EVALUATION') return 'info'
  if (type === 'TASK_DEPLOYED') return 'accent'
  if (type === 'WINDOW_FOCUS') return 'accent'
  if (type === 'DESKTOP_TERMINAL_INPUT') return 'warning'
  if (type.startsWith('TERMINAL_')) return 'info'
  if (type.startsWith('BROWSER_')) return 'info'
  if (type.startsWith('CLIPBOARD_')) return 'success'
  if (type.startsWith('ADMIN_')) return 'danger'
  if (type.startsWith('TASK_')) return 'accent'
  return 'neutral'
}

/** Human descriptions ported from legacy `renderReviewSidebar` (emoji removed). */
function eventDescription(event: RecordingEvent): string {
  const data = event.data ?? {}
  switch (event.event) {
    case 'SESSION_START':
      return `Exam started: ${str(data.name) || 'Mock Exam'}`
    case 'TASK_DEPLOYED':
      return `Task ${str(data.task_num)}: [${str(data.question_id)}] ${str(data.title)}`.trim()
    case 'TASK_FLAGGED':
      return `Flagged Task ${str(data.task_num)} (${str(data.question_id)})`
    case 'TASK_UNFLAGGED':
      return `Unflagged Task ${str(data.task_num)} (${str(data.question_id)})`
    case 'TASK_RETRY':
      return `Reset/Retry Task ${str(data.task_num)}`
    case 'TASK_EVALUATION':
      return `Evaluated [${str(data.question_id)}]: ${str(data.score)}/${str(data.max_score)} pts (${
        data.passed ? 'PASS' : 'FAIL'
      })`
    case 'EXAM_SUBMITTED':
      return `Final Submission: ${str(data.percentage)}% (${str(data.total_earned)}/${str(
        data.total_possible,
      )} pts)`
    case 'CLIPBOARD_COPY': {
      const preview = str(data.preview)
      return `Copied snippet: "${preview.substring(0, 30)}..."`
    }
    case 'TERMINAL_ATTACH':
      return 'Candidate terminal connected'
    case 'BROWSER_NAVIGATE':
      return `Visited: ${str(data.title) || str(data.url) || 'Documentation'}`
    case 'BROWSER_SEARCH':
      return `Search: "${str(data.query)}" (${str(data.domain) || 'web'})`
    default:
      return event.event
  }
}

function eventLabel(type: string): string {
  return type.replace(/^TASK_/, '')
}

function taskScore(task: TaskTimelineEntry): string {
  return task.score !== null && task.score !== undefined
    ? `${task.score}/${task.max_score ?? 0} pts`
    : 'Not graded'
}

function onScrub(event: Event): void {
  const target = event.target as HTMLInputElement
  replay.seek(Number(target.value))
}

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

/**
 * Install a parsed cast while optionally carrying the playhead and playback
 * state across the swap, so switching channels does not reset the timeline.
 */
function applyCast(text: string | null | undefined, preserve: boolean): void {
  const playhead = currentTime.value
  const wasPlaying = isPlaying.value
  const payload = typeof text === 'string' ? text : ''
  replay.loadCast(payload)
  if (preserve) {
    replay.seek(playhead)
    if (wasPlaying && currentTime.value < duration.value) replay.play()
  }
}

/**
 * Load the active channel's cast. `preserve` keeps the current playhead +
 * playing state (channel switches); otherwise the playhead resets (session
 * changes). A stale response is discarded via `castToken`. Channels without a
 * cast skip the fetch entirely so the terminal shows its empty state while the
 * event/task timeline keeps working.
 */
async function loadChannel(preserve: boolean): Promise<void> {
  if (!props.sessionId) {
    castLoading.value = false
    applyCast(props.castText, preserve)
    return
  }

  castController?.abort()
  castController = null
  castToken += 1

  if (!props.hasCast) {
    castLoading.value = false
    applyCast(null, preserve)
    return
  }

  const controller = new AbortController()
  castController = controller
  const token = ++castToken
  castLoading.value = true
  try {
    const text = await getRecordingCast(props.sessionId, props.channel, controller.signal)
    if (token !== castToken || controller.signal.aborted) return
    applyCast(typeof text === 'string' ? text : null, preserve)
  } catch {
    if (token !== castToken || controller.signal.aborted) return
    applyCast(null, preserve)
  } finally {
    if (token === castToken) castLoading.value = false
  }
}

onMounted(() => {
  const container = containerRef.value
  if (!container) return

  const term = new Terminal({
    cursorBlink: false,
    disableStdin: true,
    fontFamily: readToken('--font-mono', 'monospace'),
    fontSize: 13,
    lineHeight: 1.2,
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
  })

  void loadChannel(false)
})

watch(
  () => props.sessionId,
  () => {
    if (terminalRef.value) void loadChannel(false)
  },
)

watch(
  () => props.channel,
  () => {
    if (terminalRef.value) void loadChannel(true)
  },
)

watch(
  () => props.castText,
  (next) => {
    if (props.sessionId || !terminalRef.value) return
    applyCast(next, false)
  },
)

watch(
  () => filteredEvents.value,
  (list) => replay.setEvents(list ?? []),
  { immediate: true },
)

watch(
  () => props.hasCast,
  (next) => {
    if (next) window.requestAnimationFrame(() => fitTerminal())
  },
)

onBeforeUnmount(() => {
  replay.pause()
  castController?.abort()
  castController = null
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
  play: replay.play,
  pause: replay.pause,
  toggle: replay.toggle,
  seek: replay.seek,
  restart: replay.restart,
  setSpeed: replay.setSpeed,
})
</script>

<template>
  <div class="flex flex-col gap-3" data-testid="replay-player">
    <div class="flex flex-col gap-3 lg:flex-row">
      <!-- Event / task timeline (left) — click an entry to seek the replay -->
      <aside v-if="showTimeline" class="flex w-full flex-col gap-2 lg:w-80 lg:flex-none">
        <div class="flex flex-wrap items-center gap-2" data-testid="replay-controls">
          <div
            role="tablist"
            aria-label="Recording channels"
            class="inline-flex items-center gap-0.5 rounded-[var(--radius-md)] border border-border bg-surface p-0.5"
          >
            <Menu as="div" class="relative">
              <MenuButton
                :id="userTabId"
                type="button"
                role="tab"
                :aria-selected="!isAdmin"
                :aria-controls="panelId"
                :class="actorTabClass(!isAdmin)"
                data-testid="recording-tab-user"
              >
                User
                <Icon name="chevron-down" :size="12" class="flex-none" />
              </MenuButton>

              <Transition
                enter-active-class="transition duration-100 ease-out motion-reduce:transition-none"
                enter-from-class="opacity-0 -translate-y-1"
                enter-to-class="opacity-100 translate-y-0"
                leave-active-class="transition duration-75 ease-in motion-reduce:transition-none"
                leave-from-class="opacity-100 translate-y-0"
                leave-to-class="opacity-0 -translate-y-1"
              >
                <MenuItems
                  class="absolute left-0 z-50 mt-1 w-36 origin-top-left rounded-[var(--radius-md)] border border-border bg-elevated p-1 shadow-[var(--shadow-md)] focus:outline-none"
                  data-testid="recording-user-menu"
                >
                  <MenuItem
                    v-for="option in USER_CHANNELS"
                    :key="option.value"
                    v-slot="{ active }"
                  >
                    <button
                      type="button"
                      :class="[
                        'flex w-full items-center justify-between gap-2 rounded-[var(--radius-sm)] px-2.5 py-1.5 text-left text-sm transition-colors',
                        active ? 'bg-hover' : '',
                        channel === option.value ? 'font-medium text-accent-text' : 'text-text',
                      ]"
                      :data-testid="`recording-user-channel-${option.value}`"
                      @click="channelModel = option.value"
                    >
                      <span class="truncate">{{ option.label }}</span>
                      <Icon
                        v-if="channel === option.value"
                        name="check"
                        :size="14"
                        :stroke-width="2.5"
                        class="flex-none"
                      />
                    </button>
                  </MenuItem>
                </MenuItems>
              </Transition>
            </Menu>

            <button
              :id="adminTabId"
              type="button"
              role="tab"
              :aria-selected="isAdmin"
              :aria-controls="panelId"
              :class="actorTabClass(isAdmin)"
              data-testid="recording-tab-admin"
              @click="channelModel = 'admin-web'"
            >
              Admin
            </button>
          </div>

          <SegmentedControl
            v-model="activeTab"
            size="sm"
            :options="tabOptions"
            aria-label="Replay timeline"
          />

          <span class="ml-auto text-xs text-text-muted" data-testid="replay-count">
            {{ activeTab === 'tasks' ? `${tasks.length} tasks` : `${filteredEvents.length} events` }}
          </span>
        </div>

        <div
          :id="panelId"
          role="tabpanel"
          :aria-labelledby="isAdmin ? adminTabId : userTabId"
          class="max-h-[58vh] min-h-[220px] overflow-y-auto rounded-[var(--radius-md)] border border-border bg-elevated p-1"
          data-testid="replay-timeline"
        >
          <template v-if="activeTab === 'timeline'">
            <p v-if="filteredEvents.length === 0" class="p-3 text-sm text-text-muted">
              No events logged for this channel.
            </p>
            <ul v-else class="m-0 flex list-none flex-col gap-0.5 p-0">
              <li v-for="(event, index) in filteredEvents" :key="index">
                <button
                  type="button"
                  :class="[
                    'flex w-full flex-col gap-1 rounded-[var(--radius-sm)] border border-transparent px-2 py-1.5 text-left transition-colors hover:bg-hover',
                    index === activeEventIndex
                      ? 'border-accent/40 bg-[var(--color-accent-subtle)]'
                      : '',
                  ]"
                  data-testid="replay-event"
                  @click="replay.seek(eventTime(event))"
                >
                  <span class="flex items-center justify-between gap-2">
                    <span class="font-mono text-xs tabular-nums text-text-muted">
                      {{ event.rel_time_formatted || formatReplayTime(event.rel_time) }}
                    </span>
                    <Badge :variant="eventVariant(event.event)">{{
                      eventLabel(event.event)
                    }}</Badge>
                  </span>
                  <span class="text-xs text-text">{{ eventDescription(event) }}</span>
                </button>
              </li>
            </ul>
          </template>

          <template v-else>
            <p v-if="tasks.length === 0" class="p-3 text-sm text-text-muted">
              No task navigation recorded.
            </p>
            <ul v-else class="m-0 flex list-none flex-col gap-0.5 p-0">
              <li v-for="(task, index) in tasks" :key="task.question_id">
                <button
                  type="button"
                  :class="[
                    'flex w-full flex-col gap-1 rounded-[var(--radius-sm)] border border-transparent px-2 py-1.5 text-left transition-colors hover:bg-hover',
                    index === activeTaskIndex
                      ? 'border-accent/40 bg-[var(--color-accent-subtle)]'
                      : '',
                  ]"
                  data-testid="replay-task"
                  @click="replay.seek(taskTime(task))"
                >
                  <span class="flex items-center justify-between gap-2">
                    <span class="font-mono text-xs tabular-nums text-text-muted">
                      {{ formatReplayTime(task.first_seen_time) }}
                    </span>
                    <Badge variant="accent">Task {{ task.task_num }}</Badge>
                  </span>
                  <span class="text-xs font-semibold text-text">
                    [{{ task.question_id }}] {{ task.title }}
                  </span>
                  <span class="flex items-center justify-between gap-2 text-xs text-text-muted">
                    <span>Visits: {{ task.visits ?? 0 }}</span>
                    <span>Score: {{ taskScore(task) }}</span>
                  </span>
                  <span v-if="task.is_flagged" class="text-xs font-medium text-warning-text">
                    Flagged
                  </span>
                </button>
              </li>
            </ul>
          </template>
        </div>
      </aside>

      <!-- Terminal replay (right, dominant) + transport -->
      <div class="flex min-w-0 flex-1 flex-col gap-2">
        <div class="flex h-[22px] items-center justify-between gap-2">
          <span class="text-sm font-medium text-text">Terminal replay</span>
          <span class="font-mono text-xs tabular-nums text-text-muted" data-testid="replay-time">
            {{ formatReplayTime(currentTime) }} / {{ formatReplayTime(duration) }}
          </span>
        </div>

        <div
          ref="container"
          :class="[
            'h-[58vh] min-h-[280px] w-full overflow-hidden rounded-[var(--radius-md)] border border-border bg-app p-1',
            hasCast ? '' : 'hidden',
          ]"
          role="group"
          :aria-label="ariaLabel"
          data-testid="replay-terminal"
        ></div>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="primary"
            :disabled="!hasFrames"
            :aria-label="isPlaying ? 'Pause replay' : 'Play replay'"
            data-testid="replay-play-toggle"
            @click="replay.toggle()"
          >
            <Icon :name="isPlaying ? 'pause' : 'play'" :size="14" />
            {{ isPlaying ? 'Pause' : 'Play' }}
          </Button>

          <Button
            size="sm"
            variant="secondary"
            :disabled="!hasFrames"
            aria-label="Back 10 seconds"
            data-testid="replay-back-10"
            @click="replay.seekRelative(-10)"
          >
            -10s
          </Button>

          <Button
            size="sm"
            variant="secondary"
            :disabled="!hasFrames"
            aria-label="Forward 10 seconds"
            data-testid="replay-forward-10"
            @click="replay.seekRelative(10)"
          >
            +10s
          </Button>

          <Button
            size="sm"
            variant="secondary"
            :disabled="!hasFrames"
            data-testid="replay-restart"
            @click="replay.restart()"
          >
            <Icon name="refresh" :size="14" />
            Restart
          </Button>

          <div class="ml-auto flex items-center gap-2">
            <span class="text-xs text-text-muted">Speed</span>
            <div class="w-20">
              <Select v-model="speedModel" :options="SPEED_OPTIONS" aria-label="Replay speed" />
            </div>
          </div>
        </div>

        <label class="flex items-center gap-2">
          <span class="sr-only">Replay position</span>
          <input
            type="range"
            min="0"
            :max="Math.max(1, duration)"
            step="0.1"
            :value="currentTime"
            :disabled="!hasFrames"
            class="h-1.5 w-full cursor-pointer accent-[var(--color-accent)] disabled:cursor-not-allowed disabled:opacity-60"
            data-testid="replay-scrubber"
            @input="onScrub"
          />
        </label>
      </div>
    </div>

    <p
      v-if="castLoading"
      class="m-0 flex items-center gap-2 text-sm text-text-muted"
      data-testid="replay-loading"
    >
      <Spinner size="sm" /> Loading terminal recording…
    </p>

    <p
      v-else-if="!hasCast"
      class="m-0 text-sm text-text-muted"
      data-testid="recording-no-cast"
    >
      No recording for this terminal.
    </p>

    <p v-else-if="!hasFrames" class="m-0 text-sm text-text-muted" data-testid="replay-empty">
      No terminal recording is available for this session.
    </p>
  </div>
</template>
