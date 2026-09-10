<script setup lang="ts">
import { computed } from 'vue'

import MarkdownRenderer from '@/components/MarkdownRenderer.vue'
import { Badge } from '@/components/ui'

import { taskBadges, type TaskPaneTask } from './task'

/**
 * TaskPane (FE-022) — the candidate's left-pane task view: a compact header with
 * metadata/status badges and the sanitized markdown instructions below.
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
  }>(),
  { task: null, emptyText: 'No active task.' },
)

const emit = defineEmits<{ copy: [text: string] }>()

const badges = computed(() => (props.task ? taskBadges(props.task) : []))
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
  </section>
</template>
