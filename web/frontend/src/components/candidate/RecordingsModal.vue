<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import {
  getRecording,
  listRecordings,
  recordingEventsUrl,
} from '@/api/recordings'
import type { RecordingChannel, RecordingDetail, RecordingSummary } from '@/api/recordings'
import { Badge, Button, DISABLED, FOCUS_RING, Icon, Modal, Spinner } from '@/components/ui'
import type { BadgeVariant } from '@/components/ui'
import ReplayPlayer from '@/components/workspace/ReplayPlayer.vue'
import { formatReplayTime } from '@/composables/useReplay'

/**
 * RecordingsModal (FE-029) — the candidate "Recordings & review" surface.
 *
 * Opens from the header overflow `recordings` action (legacy
 * `openRecordingsModal`) and shows two views in one dialog:
 *
 *   1. list   — `GET /api/recordings` rows (session, exam/preset, date,
 *               duration, score, status) with review + `.cast`/events downloads;
 *   2. detail — `GET /api/recordings/{id}` + `/cast`, rendering `ReplayPlayer`
 *               with the event log / task timeline and download links.
 *
 * Strict parity (D-007): same routes, same review → replay flow as the legacy
 * `openReviewModal`, with native dialogs/emoji replaced by the design system.
 */

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    description?: string
    /**
     * Open directly on this session's replay instead of the recordings list.
     * Used by the admin observe overlay ("Review & Replay", legacy
     * `openReviewModal(currentObserveSessionId)`).
     */
    initialSessionId?: string
    /** Show event counts/logs. The admin observe review hides them. Default `true`. */
    showEvents?: boolean
    /**
     * Show the all-sessions recordings list + "Back to list". Set `false` when
     * the modal is scoped to a single observed session.
     */
    showList?: boolean
  }>(),
  {
    title: 'Recordings & review',
    description: 'Replay a recorded candidate session and inspect its timeline.',
    initialSessionId: '',
    showEvents: true,
    showList: true,
  },
)

const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()

const recordings = ref<RecordingSummary[]>([])
const listLoading = ref(false)
const listError = ref('')

const selectedId = ref<string | null>(null)
const detail = ref<RecordingDetail | null>(null)
const detailLoading = ref(false)
const detailError = ref('')

/**
 * Selected recording channel (`user-web` | `user-desktop` | `admin-web`).
 * `ReplayPlayer` owns the actor/channel selector and emits `update:channel`;
 * this modal owns the state and the per-session scoping.
 */
const channel = ref('user-web')

let listController: AbortController | null = null
let detailController: AbortController | null = null

const activeSessionId = computed(() => selectedId.value ?? '')
const dialogTitle = computed(() =>
  selectedId.value ? `Session review: ${selectedId.value}` : props.title,
)
const dialogDescription = computed(() => (selectedId.value ? null : props.description))

const channels = computed<RecordingChannel[]>(() => detail.value?.channels ?? [])
const hasChannelMeta = computed(() => channels.value.length > 0)

function channelMeta(id: string): RecordingChannel | undefined {
  return channels.value.find((channel) => channel.id === id)
}

/** Whether the currently selected channel has a downloadable/replayable cast. */
const selectedHasCast = computed(() => {
  if (!hasChannelMeta.value) return detail.value?.has_cast ?? true
  return channelMeta(channel.value)?.has_cast ?? false
})

function abortList(): void {
  listController?.abort()
  listController = null
}

function abortDetail(): void {
  detailController?.abort()
  detailController = null
}

async function loadList(): Promise<void> {
  abortList()
  const controller = new AbortController()
  listController = controller
  listLoading.value = true
  listError.value = ''
  try {
    const response = await listRecordings(controller.signal)
    if (controller.signal.aborted) return
    recordings.value = response.recordings ?? []
  } catch (error) {
    if (controller.signal.aborted) return
    listError.value = error instanceof Error ? error.message : 'Failed to load recordings'
  } finally {
    if (listController === controller) {
      listLoading.value = false
      listController = null
    }
  }
}

async function openRecording(sessionId: string): Promise<void> {
  abortDetail()
  selectedId.value = sessionId
  detail.value = null
  detailError.value = ''
  channel.value = 'user-web'
  detailLoading.value = true
  const controller = new AbortController()
  detailController = controller
  try {
    const meta = await getRecording(sessionId, controller.signal)
    if (controller.signal.aborted) return
    detail.value = meta
  } catch (error) {
    if (controller.signal.aborted) return
    detailError.value = error instanceof Error ? error.message : 'Failed to load recording'
  } finally {
    if (detailController === controller) {
      detailLoading.value = false
      detailController = null
    }
  }
}

function backToList(): void {
  abortDetail()
  selectedId.value = null
  detail.value = null
  detailError.value = ''
  detailLoading.value = false
}

function examName(recording: RecordingSummary): string {
  return recording.preset || recording.name || 'Mock Exam'
}

function formatDate(value: string | null | undefined): string {
  if (!value) return 'Unknown'
  return value.substring(0, 19).replace('T', ' ')
}

function durationLabel(recording: RecordingSummary): string {
  if (recording.duration_formatted) return recording.duration_formatted
  if (recording.duration_seconds) return formatReplayTime(recording.duration_seconds)
  return '--:--'
}

function scoreLabel(recording: RecordingSummary): string {
  return recording.percentage !== null && recording.percentage !== undefined
    ? `${recording.percentage}%`
    : '--'
}

function statusVariant(recording: RecordingSummary): BadgeVariant {
  if (recording.passed === true) return 'success'
  if (recording.passed === false) return 'danger'
  return 'warning'
}

function statusLabel(recording: RecordingSummary): string {
  if (recording.passed === true) return 'Passed'
  if (recording.passed === false) return 'Failed'
  return 'In Progress'
}

function detailStatus(): string {
  if (!detail.value) return ''
  if (detail.value.passed === true) return 'PASSED'
  if (detail.value.passed === false) return 'FAILED'
  return 'IN PROGRESS'
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      backToList()
      void loadList()
      if (props.initialSessionId) void openRecording(props.initialSessionId)
    } else {
      abortList()
      abortDetail()
    }
  },
)

onBeforeUnmount(() => {
  abortList()
  abortDetail()
})
</script>

<template>
  <Modal
    :model-value="modelValue"
    :title="dialogTitle"
    :description="dialogDescription ?? undefined"
    size="xl"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <!-- List view -->
    <div v-if="showList && !selectedId" class="flex flex-col gap-3" data-testid="recordings-list">
      <div v-if="listLoading" class="flex items-center gap-2 py-6 text-sm text-text-muted">
        <Spinner size="sm" /> Loading candidate recordings…
      </div>

      <p v-else-if="listError" class="py-4 text-sm text-danger-text">
        Failed to load recordings: {{ listError }}
      </p>

      <p v-else-if="recordings.length === 0" class="py-4 text-sm text-text-muted">
        No candidate session recordings found yet. Complete or submit an exam drill to generate
        recordings.
      </p>

      <ul v-else class="m-0 flex max-h-[62vh] list-none flex-col gap-2 overflow-y-auto p-0">
        <li
          v-for="recording in recordings"
          :key="recording.session_id"
          class="rounded-[var(--radius-md)] border border-border bg-surface p-3"
          data-testid="recording-row"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="truncate font-mono text-xs text-accent-text">
                {{ recording.session_id }}
              </div>
              <div class="truncate text-sm font-semibold text-text">
                {{ examName(recording) }}
              </div>
            </div>
            <Badge :variant="statusVariant(recording)" copyable :copy-text="statusLabel(recording)">
              {{ statusLabel(recording) }}
            </Badge>
          </div>

          <dl class="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-4">
            <div class="min-w-0">
              <dt class="text-text-muted">Date</dt>
              <dd class="m-0 truncate text-text">{{ formatDate(recording.started_at) }}</dd>
            </div>
            <div class="min-w-0">
              <dt class="text-text-muted">Duration</dt>
              <dd class="m-0 tabular-nums text-text">{{ durationLabel(recording) }}</dd>
            </div>
            <div class="min-w-0">
              <dt class="text-text-muted">Score</dt>
              <dd class="m-0 tabular-nums text-text">{{ scoreLabel(recording) }}</dd>
            </div>
            <div v-if="showEvents" class="min-w-0">
              <dt class="text-text-muted">Events</dt>
              <dd class="m-0 tabular-nums text-text">{{ recording.events_count ?? 0 }}</dd>
            </div>
          </dl>

          <div class="mt-3 flex flex-wrap items-center gap-2">
            <Button
              size="sm"
              variant="primary"
              data-testid="recording-review"
              @click="openRecording(recording.session_id)"
            >
              <Icon name="play" :size="14" />
              Review &amp; replay
            </Button>
            <a
              v-if="recording.has_events"
              :href="recordingEventsUrl(recording.session_id)"
              :download="`${recording.session_id}.events.json`"
              :class="[
                'inline-flex h-8 select-none items-center justify-center gap-1.5 rounded-[var(--radius-sm)] border border-border bg-surface px-3 text-xs font-semibold text-text transition-colors hover:bg-hover',
                FOCUS_RING,
                DISABLED,
              ]"
            >
              Download events
            </a>
          </div>
        </li>
      </ul>
    </div>

    <!-- Detail / replay view -->
    <div v-else class="flex flex-col gap-3" data-testid="recording-detail">
      <div class="flex flex-wrap items-center gap-2">
        <Button
          v-if="showList"
          variant="ghost"
          size="sm"
          data-testid="recording-back"
          @click="backToList"
        >
          <Icon name="chevron-left" :size="14" />
          Back to list
        </Button>
        <div class="ml-auto flex flex-wrap items-center gap-2">
          <a
            v-if="detail?.has_events"
            :href="recordingEventsUrl(activeSessionId)"
            :download="`${activeSessionId}.events.json`"
            :class="[
              'inline-flex h-8 select-none items-center justify-center gap-1.5 rounded-[var(--radius-sm)] border border-border bg-surface px-3 text-xs font-semibold text-text transition-colors hover:bg-hover',
              FOCUS_RING,
              DISABLED,
            ]"
          >
            Download events
          </a>
        </div>
      </div>

      <div v-if="detailLoading" class="flex items-center gap-2 py-6 text-sm text-text-muted">
        <Spinner size="sm" /> Loading session data, timeline, and terminal recording…
      </div>

      <p v-else-if="detailError" class="py-4 text-sm text-danger-text">
        Error loading session: {{ detailError }}
      </p>

      <template v-else-if="detail">
        <dl class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-4">
          <div class="min-w-0">
            <dt class="text-text-muted">Exam</dt>
            <dd class="m-0 truncate text-text">{{ examName(detail) }}</dd>
          </div>
          <div class="min-w-0">
            <dt class="text-text-muted">Result</dt>
            <dd class="m-0 text-text">{{ detailStatus() }} ({{ scoreLabel(detail) }})</dd>
          </div>
          <div class="min-w-0">
            <dt class="text-text-muted">Duration</dt>
            <dd class="m-0 tabular-nums text-text">{{ durationLabel(detail) }}</dd>
          </div>
          <div v-if="showEvents" class="min-w-0">
            <dt class="text-text-muted">Total events</dt>
            <dd class="m-0 tabular-nums text-text">{{ detail.events_count ?? 0 }}</dd>
          </div>
        </dl>

        <div class="flex flex-col gap-3" data-testid="recording-channels">
          <ReplayPlayer
            :session-id="activeSessionId"
            :channel="channel"
            :has-cast="selectedHasCast"
            :events="detail.events ?? []"
            :tasks="detail.task_timeline ?? []"
            :duration-fallback="detail.duration_seconds ?? 0"
            :show-events="showEvents"
            @update:channel="channel = $event"
          />
        </div>
      </template>
    </div>

    <template #footer>
      <Button variant="secondary" @click="emit('update:modelValue', false)">Close</Button>
    </template>
  </Modal>
</template>
