<script setup lang="ts">
import { computed } from 'vue'

import type { Preset } from '@/api/presets'
import { Badge, Button, FOCUS_RING, Modal } from '@/components/ui'

/**
 * PresetModal (FE-024) — the exam preset selector (admin) plus the
 * full-curriculum card.
 *
 * Cards show the preset name, description and metadata (time limit, task count,
 * pass threshold) using plain text labels only — no emoji — and the design
 * system tokens. The full-curriculum card maps to the `all` preset filename used
 * by `POST /api/presets/select` (legacy `selectFullCurriculum`).
 */

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    presets: Preset[]
    selected?: string | null
    loading?: boolean
    title?: string
    description?: string
    showFullCurriculum?: boolean
    fullCurriculumTaskCount?: number
  }>(),
  {
    selected: null,
    loading: false,
    title: 'Select a preset',
    description: 'Choose the exam preset to run.',
    showFullCurriculum: true,
    fullCurriculumTaskCount: 111,
  },
)

const emit = defineEmits<{ 'update:modelValue': [value: boolean]; select: [filename: string] }>()

const fullSelected = computed(() => props.selected === 'all')

function isSelected(preset: Preset): boolean {
  return props.selected === preset.filename
}

function taskCount(preset: Preset): number {
  return preset.task_count ?? preset.questions?.length ?? 0
}

function timeLimitLabel(preset: Preset): string {
  return preset.time_limit_minutes ? `${preset.time_limit_minutes} minutes` : 'Untimed'
}

function passLabel(preset: Preset): string {
  return `${preset.pass_threshold_percent ?? 66}%`
}

function pick(filename: string): void {
  emit('select', filename)
  emit('update:modelValue', false)
}

function close(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <Modal :model-value="modelValue" :title="title" :description="description" size="lg" @update:model-value="close">
    <div v-if="loading" class="py-8 text-center text-sm text-text-muted">Loading presets…</div>

    <ul
      v-else
      class="preset-list m-0 flex max-h-[60vh] list-none flex-col gap-2 overflow-auto p-0"
      data-testid="preset-list"
    >
      <li v-for="preset in presets" :key="preset.filename">
        <button
          type="button"
          data-testid="preset-card"
          :data-filename="preset.filename"
          :aria-pressed="isSelected(preset) ? 'true' : 'false'"
          :class="[
            'flex w-full flex-col gap-1 rounded-[var(--radius-md)] border px-3 py-2.5 text-left transition-colors',
            isSelected(preset)
              ? 'border-accent bg-[var(--color-accent-subtle)]'
              : 'border-border bg-surface hover:bg-hover',
            FOCUS_RING,
          ]"
          @click="pick(preset.filename)"
        >
          <span class="flex w-full items-center justify-between gap-2">
            <span class="truncate text-sm font-semibold text-text" :title="preset.name || preset.filename">
              {{ preset.name || preset.filename }}
            </span>
            <Badge v-if="isSelected(preset)" variant="success">Selected</Badge>
          </span>
          <span class="text-sm text-text-muted">
            {{ preset.description || 'Practice exam tasks.' }}
          </span>
          <span class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-muted">
            <span>Time limit: {{ timeLimitLabel(preset) }}</span>
            <span>Tasks: {{ taskCount(preset) }}</span>
            <span>Pass: {{ passLabel(preset) }}</span>
          </span>
        </button>
      </li>

      <li v-if="showFullCurriculum">
        <button
          type="button"
          data-testid="full-curriculum-card"
          data-filename="all"
          :aria-pressed="fullSelected ? 'true' : 'false'"
          :class="[
            'flex w-full flex-col gap-1 rounded-[var(--radius-md)] border px-3 py-2.5 text-left transition-colors',
            fullSelected
              ? 'border-accent bg-[var(--color-accent-subtle)]'
              : 'border-border-strong bg-elevated hover:bg-hover',
            FOCUS_RING,
          ]"
          @click="pick('all')"
        >
          <span class="flex w-full items-center justify-between gap-2">
            <span class="text-sm font-semibold text-text">Full Curriculum</span>
            <Badge v-if="fullSelected" variant="success">Selected</Badge>
          </span>
          <span class="text-sm text-text-muted">
            Practice every task in sequential order.
          </span>
          <span class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-text-muted">
            <span>Time limit: Untimed</span>
            <span>Tasks: {{ fullCurriculumTaskCount }}</span>
            <span>Pass: 66%</span>
          </span>
        </button>
      </li>
    </ul>

    <template #footer>
      <Button variant="secondary" @click="close">Cancel</Button>
    </template>
  </Modal>
</template>

<style scoped>
/* Slim, token-coloured scrollbar so the preset list matches the design system
 * instead of the default OS chrome. Firefox uses the standard properties;
 * Chromium/WebKit use the pseudo-elements. */
.preset-list {
  scrollbar-width: thin;
  scrollbar-color: var(--color-border-strong) transparent;
}

.preset-list::-webkit-scrollbar {
  width: 10px;
}

.preset-list::-webkit-scrollbar-track {
  background: transparent;
}

.preset-list::-webkit-scrollbar-thumb {
  background-color: var(--color-border-strong);
  border: 2px solid transparent;
  border-radius: var(--radius-full);
  background-clip: content-box;
}

.preset-list::-webkit-scrollbar-thumb:hover {
  background-color: var(--color-text-dim);
}
</style>
