<script setup lang="ts">
import { computed } from 'vue'

import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { Badge, Button, Icon } from '@/components/ui'

import { taskBadges, type TaskPaneTask } from './task'

/**
 * TaskPane (FE-022) — the candidate's left-pane task view: a compact header with
 * metadata/status badges, the sanitized markdown instructions below, and the
 * legacy navigation footer (Previous · Reset task · Task X of Y · Next).
 *
 * Colours come from FE-012 tokens only (Badge variants); no raw hex, glow or
 * emoji. The markdown body is delegated to `MarkdownRenderer`, which sanitizes
 * with DOMPurify and wires inline/block code copy. A code copy is re-emitted so
 * the workspace can mirror it into the noVNC desktop clipboard (legacy
 * `copyCode`/`copyInlineCode` called `syncTextToVnc`).
 */

const props = withDefaults(
  defineProps<{
    task?: TaskPaneTask | null
    emptyText?: string
    taskNum?: number
    totalTasks?: number
    busy?: boolean
  }>(),
  { task: null, emptyText: 'No active task.', taskNum: 0, totalTasks: 0, busy: false },
)

const emit = defineEmits<{
  copy: [text: string]
  prev: []
  next: []
  reset: []
}>()

const badges = computed(() => (props.task ? taskBadges(props.task) : []))
const prevDisabled = computed(() => props.busy || props.taskNum <= 1)
const nextDisabled = computed(
  () => props.busy || (props.totalTasks > 0 && props.taskNum >= props.totalTasks),
)
</script>

<template>
  <section class="flex h-full min-h-0 flex-col bg-surface text-text">
    <header v-if="task" class="flex-none border-b border-border px-4 py-3">
      <div class="flex flex-wrap items-center gap-1.5">
        <Badge
          v-for="badge in badges"
          :key="badge.key"
          :variant="badge.variant"
          copyable
          :copy-text="badge.copy ?? badge.label"
        >
          {{ badge.label }}
        </Badge>
      </div>
      <h1 class="mt-2 truncate text-lg font-semibold text-text" :title="task.title">
        {{ task.title }}
      </h1>
    </header>

    <div class="min-h-0 flex-1 overflow-auto px-4 py-3">
      <MarkdownRenderer
        v-if="task"
        :source="task.description"
        :empty-text="emptyText"
        @copy="emit('copy', $event)"
      />
      <p v-else class="text-text-muted">{{ emptyText }}</p>
    </div>

    <footer
      v-if="task"
      class="flex flex-none items-center gap-2 border-t border-border px-4 py-2"
      data-testid="task-footer"
    >
      <Button
        variant="secondary"
        size="sm"
        :disabled="prevDisabled"
        data-testid="task-prev"
        @click="emit('prev')"
      >
        <Icon name="chevron-left" :size="16" />
        Previous
      </Button>
      <Button
        variant="secondary"
        size="sm"
        :disabled="busy"
        data-testid="task-reset"
        @click="emit('reset')"
      >
        Reset task
      </Button>
      <span
        class="flex-1 text-center text-xs tabular-nums text-text-muted"
        data-testid="task-progress-text"
      >
        Task {{ taskNum }} of {{ totalTasks }}
      </span>
      <Button
        variant="secondary"
        size="sm"
        :disabled="nextDisabled"
        data-testid="task-next"
        @click="emit('next')"
      >
        Next
        <Icon name="chevron-right" :size="16" />
      </Button>
    </footer>
  </section>
</template>
