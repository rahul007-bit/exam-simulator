<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { Badge, Button, FOCUS_RING, Modal, Spinner } from '@/components/ui'

import {
  fetchQuestions,
  navState,
  navStateLabel,
  navStateVariant,
  navSummary,
  type NavState,
  type QuestionNavItem,
} from './question'

/**
 * QuestionDrawer (FE-024) — the candidate question navigator shown in a Modal.
 *
 * Each task reflects its effective state (current / flagged / scored / pending)
 * with a Badge and a token-coloured card; clicking a task jumps to it. When the
 * `questions` prop is omitted the drawer loads `GET /api/questions` on open.
 * Colours come from FE-012 tokens only (no raw hex, glow or emoji).
 */

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    questions?: QuestionNavItem[] | null
    loading?: boolean
    title?: string
    emptyText?: string
    loadOnOpen?: boolean
    load?: (signal?: AbortSignal) => Promise<QuestionNavItem[]>
  }>(),
  {
    questions: undefined,
    loading: false,
    title: 'Question navigator',
    emptyText: 'No questions available.',
    loadOnOpen: true,
    load: undefined,
  },
)

const emit = defineEmits<{ 'update:modelValue': [value: boolean]; select: [taskNum: number] }>()

const loaded = ref<QuestionNavItem[]>([])
const internalLoading = ref(false)
const error = ref<string | null>(null)

const controlled = computed(() => props.questions !== undefined)
const items = computed<QuestionNavItem[]>(() =>
  controlled.value ? (props.questions ?? []) : loaded.value,
)
const isLoading = computed(() => props.loading || internalLoading.value)
const summary = computed(() => navSummary(items.value))

const CARD_TONES: Record<NavState, string> = {
  current: 'border-accent bg-[var(--color-accent-subtle)]',
  flagged: 'border-warning-text/40 bg-warning/10',
  scored: 'border-info-text/40 bg-info/10',
  pending: 'border-border bg-surface hover:bg-hover',
}

function state(item: QuestionNavItem): NavState {
  return navState(item)
}

function label(item: QuestionNavItem): string {
  return navStateLabel(navState(item))
}

function variant(item: QuestionNavItem) {
  return navStateVariant(navState(item))
}

function cardClass(item: QuestionNavItem): string {
  return [
    'flex w-full flex-col items-start gap-1 rounded-[var(--radius-md)] border px-3 py-2 text-left transition-colors',
    CARD_TONES[navState(item)],
    FOCUS_RING,
  ].join(' ')
}

async function loadItems(): Promise<void> {
  if (internalLoading.value) return
  internalLoading.value = true
  error.value = null
  try {
    const loader = props.load ?? fetchQuestions
    loaded.value = await loader()
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
  } finally {
    internalLoading.value = false
  }
}

function close(): void {
  emit('update:modelValue', false)
}

function selectTask(item: QuestionNavItem): void {
  emit('select', item.task_num)
  close()
}

// Legacy `openQuestionDrawer()` re-fetched `/api/questions` on every open so the
// navigator reflects the current task after a jump; mirror that by always
// reloading (uncontrolled mode) rather than caching the first result.
watch(
  () => props.modelValue,
  (open) => {
    if (open && !controlled.value && props.loadOnOpen) {
      void loadItems()
    }
  },
  { immediate: true },
)
</script>

<template>
  <Modal :model-value="modelValue" :title="title" size="lg" @update:model-value="close">
    <div class="flex flex-wrap items-center gap-1.5" data-testid="question-nav-summary">
      <Badge variant="neutral" copyable :copy-text="`${summary.total} tasks`">
        {{ summary.total }} tasks
      </Badge>
      <Badge variant="accent" copyable :copy-text="`${summary.current} current`">
        {{ summary.current }} current
      </Badge>
      <Badge variant="warning" copyable :copy-text="`${summary.flagged} flagged`">
        {{ summary.flagged }} flagged
      </Badge>
      <Badge variant="info" copyable :copy-text="`${summary.scored} scored`">
        {{ summary.scored }} scored
      </Badge>
    </div>

    <div v-if="isLoading" class="flex justify-center py-8" data-testid="question-nav-loading">
      <Spinner label="Loading questions" />
    </div>

    <p v-else-if="error" class="mt-3 text-sm text-danger-text" role="alert">{{ error }}</p>

    <p v-else-if="items.length === 0" class="mt-3 text-sm text-text-muted">{{ emptyText }}</p>

    <ul
      v-else
      class="mt-3 grid max-h-[60vh] grid-cols-1 gap-2 overflow-auto sm:grid-cols-2 lg:grid-cols-3"
      data-testid="question-nav-grid"
    >
      <li v-for="item in items" :key="item.task_num">
        <div
          role="button"
          tabindex="0"
          data-testid="question-nav-item"
          :data-state="state(item)"
          :aria-current="item.is_current ? 'true' : undefined"
          :class="cardClass(item)"
          @click="selectTask(item)"
          @keydown.enter="selectTask(item)"
          @keydown.space.prevent="selectTask(item)"
        >
          <span class="flex w-full items-center justify-between gap-2">
            <span class="text-xs font-semibold text-text-muted">Task {{ item.task_num }}</span>
            <Badge :variant="variant(item)" copyable :copy-text="label(item)">{{ label(item) }}</Badge>
          </span>
          <span class="w-full truncate text-sm font-medium text-text" :title="item.title">
            {{ item.title }}
          </span>
          <span class="text-xs text-text-muted">
            {{ item.points ?? 0 }} pts
            <template v-if="item.target_context"> · context: {{ item.target_context }}</template>
          </span>
        </div>
      </li>
    </ul>

    <template #footer>
      <Button variant="secondary" @click="close">Close</Button>
    </template>
  </Modal>
</template>
