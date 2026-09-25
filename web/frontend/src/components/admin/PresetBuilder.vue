<script setup lang="ts">
import { computed, ref } from 'vue'

import { generatePreset } from '@/api/presets'
import type { GenerateDifficulty, GenerateDomain, GeneratePresetRequest } from '@/api/presets'
import { Button, Card, Input, Select } from '@/components/ui'
import type { SelectOption } from '@/components/ui'
import { useToast } from '@/composables/useToast'
import { useSessionStore } from '@/stores/session'

/**
 * PresetBuilder (FS-007) — admin "Custom exam" card.
 *
 * Collects a task count plus optional difficulty and domain filters and calls
 * `POST /api/presets/generate` (FS-006), which starts an ephemeral exam. The
 * builder never lists or previews individual questions: the only output is a
 * one-line summary of the started session.
 */

const MIN_COUNT = 1
const MAX_COUNT = 50
const DEFAULT_COUNT = 5

const DIFFICULTY_OPTIONS: SelectOption[] = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
  { value: 'crazy', label: 'Crazy' },
]

const DOMAIN_OPTIONS: { value: GenerateDomain; label: string }[] = [
  { value: 'troubleshooting', label: 'Troubleshooting' },
  { value: 'storage', label: 'Storage' },
  { value: 'workloads', label: 'Workloads' },
  { value: 'cluster-arch', label: 'Cluster architecture' },
  { value: 'security', label: 'Security' },
]

const session = useSessionStore()
const { push } = useToast()

const countInput = ref(String(DEFAULT_COUNT))
const difficulty = ref('')
const domains = ref<GenerateDomain[]>([])
const generating = ref(false)
const touched = ref(false)
const summary = ref<string | null>(null)

const countError = computed<string | null>(() => {
  const raw = countInput.value.trim()
  if (raw === '') return `Enter a whole number between ${MIN_COUNT} and ${MAX_COUNT}.`
  const parsed = Number(raw)
  if (!Number.isInteger(parsed)) return `Count must be a whole number between ${MIN_COUNT} and ${MAX_COUNT}.`
  if (parsed < MIN_COUNT || parsed > MAX_COUNT) {
    return `Count must be between ${MIN_COUNT} and ${MAX_COUNT}.`
  }
  return null
})

const showCountError = computed(() => (touched.value ? (countError.value ?? undefined) : undefined))

function onToggleDomain(value: GenerateDomain): void {
  if (domains.value.includes(value)) {
    domains.value = domains.value.filter((domain) => domain !== value)
  } else {
    domains.value = [...domains.value, value]
  }
}

function buildRequest(): GeneratePresetRequest {
  const body: GeneratePresetRequest = { count: Number(countInput.value) }
  if (difficulty.value) body.difficulty = difficulty.value as GenerateDifficulty
  if (domains.value.length > 0) body.domains = [...domains.value]
  return body
}

async function onGenerate(): Promise<void> {
  if (generating.value) return
  touched.value = true
  if (countError.value) {
    push({ variant: 'warning', message: countError.value })
    return
  }

  generating.value = true
  summary.value = null
  try {
    const response = await generatePreset(buildRequest())
    session.apply(response)
    const total = response.active === true ? response.total_tasks : Number(countInput.value)
    summary.value = `Started session with ${total} task${total === 1 ? '' : 's'}`
    push({ variant: 'success', message: summary.value })
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : String(cause)
    push({ variant: 'error', title: 'Could not generate exam', message })
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <Card
    title="Custom exam"
    subtitle="Generate and start an exam from a task count and optional filters. Questions are never shown here."
  >
    <form class="flex flex-col gap-4" novalidate @submit.prevent="onGenerate">
      <Input
        v-model="countInput"
        type="number"
        label="Number of tasks"
        :hint="`Between ${MIN_COUNT} and ${MAX_COUNT}.`"
        :error="showCountError"
        :disabled="generating"
        data-testid="preset-builder-count"
      />

      <Select
        v-model="difficulty"
        :options="DIFFICULTY_OPTIONS"
        label="Difficulty"
        placeholder="Any difficulty"
        :disabled="generating"
        data-testid="preset-builder-difficulty"
      />

      <fieldset class="flex flex-col gap-1.5 border-0 p-0" :disabled="generating">
        <legend class="mb-1.5 text-sm font-medium text-text">
          Domains
          <span class="font-normal text-text-muted">(optional)</span>
        </legend>
        <div class="flex flex-wrap gap-2">
          <label
            v-for="option in DOMAIN_OPTIONS"
            :key="option.value"
            class="cursor-pointer"
            :class="{ 'cursor-not-allowed opacity-60': generating }"
          >
            <input
              type="checkbox"
              class="peer sr-only"
              :value="option.value"
              :checked="domains.includes(option.value)"
              :disabled="generating"
              :data-testid="`preset-builder-domain-${option.value}`"
              @change="onToggleDomain(option.value)"
            />
            <span
              class="inline-flex items-center rounded-[var(--radius-full)] border border-border bg-surface px-2.5 py-1 text-sm font-medium text-text transition-colors hover:bg-hover peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-[var(--focus-ring-color)] peer-checked:border-accent/40 peer-checked:bg-[var(--color-accent-subtle)] peer-checked:text-accent-text"
            >
              {{ option.label }}
            </span>
          </label>
        </div>
      </fieldset>

      <div class="flex items-center justify-between gap-3">
        <p
          v-if="summary"
          class="m-0 text-sm text-success-text"
          role="status"
          data-testid="preset-builder-summary"
        >
          {{ summary }}
        </p>
        <span v-else></span>

        <Button
          type="submit"
          variant="primary"
          :loading="generating"
          :disabled="generating"
          data-testid="preset-builder-generate"
        >
          Generate &amp; start
        </Button>
      </div>
    </form>
  </Card>
</template>
