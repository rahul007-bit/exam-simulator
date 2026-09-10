<script setup lang="ts">
import { computed } from 'vue'

import type { SubmitResponse } from '@/api/actions'
import { Badge, Card } from '@/components/ui'

import { scorecardRows, scorecardSummary } from './scorecard'

/**
 * ExamScorecard (FE-024) — the final report returned by `POST /api/action/submit`.
 *
 * Renders the summary (percentage, points, pass/fail against the threshold) and a
 * row per submitted task with the exact payload fields
 * `task_num, id, title, domain, context, score, max_score, passed, message`.
 * Pass/fail is shown only here, after submission — never during the exam.
 */

const props = withDefaults(
  defineProps<{
    result: SubmitResponse | null
    title?: string
  }>(),
  { title: 'Exam scorecard' },
)

const rows = computed(() => scorecardRows(props.result))
const summary = computed(() => scorecardSummary(props.result))
</script>

<template>
  <section class="flex flex-col gap-4" data-testid="scorecard">
    <div
      class="flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-lg)] border border-border bg-surface px-4 py-3"
      data-testid="scorecard-summary"
    >
      <div class="flex items-center gap-3">
        <span class="text-3xl font-semibold text-text" data-testid="scorecard-percentage">
          {{ summary.percentage }}%
        </span>
        <Badge
          :variant="summary.passed ? 'success' : 'danger'"
          size="md"
          copyable
          :copy-text="summary.passed ? 'PASSED' : 'FAILED'"
        >
          {{ summary.passed ? 'PASSED' : 'FAILED' }}
        </Badge>
      </div>
      <div class="text-right text-sm text-text-muted">
        <p class="m-0" data-testid="scorecard-totals">
          {{ summary.totalEarned }} / {{ summary.totalPossible }} points earned
        </p>
        <p class="m-0">Pass threshold: {{ summary.threshold }}%</p>
      </div>
    </div>

    <Card :title="title" padding="none">
      <div v-if="!result || rows.length === 0" class="px-4 py-6 text-sm text-text-muted">
        No submissions to display.
      </div>

      <div v-else class="overflow-auto">
        <table class="w-full border-collapse text-sm" data-testid="scorecard-table">
          <thead>
            <tr class="border-b border-border text-left text-xs uppercase tracking-wide text-text-muted">
              <th class="px-3 py-2 font-medium">#</th>
              <th class="px-3 py-2 font-medium">ID</th>
              <th class="px-3 py-2 font-medium">Title</th>
              <th class="px-3 py-2 font-medium">Domain</th>
              <th class="px-3 py-2 font-medium">Context</th>
              <th class="px-3 py-2 text-right font-medium">Score</th>
              <th class="px-3 py-2 font-medium">Result</th>
              <th class="px-3 py-2 font-medium">Message</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in rows"
              :key="row.id"
              class="border-b border-border last:border-b-0"
              data-testid="scorecard-row"
            >
              <td class="px-3 py-2 text-text-muted">{{ row.task_num }}</td>
              <td class="px-3 py-2" data-testid="scorecard-id">
                <code class="rounded-[var(--radius-sm)] bg-hover px-1.5 py-0.5 text-xs text-text">{{
                  row.id
                }}</code>
              </td>
              <td class="px-3 py-2 font-medium text-text" data-testid="scorecard-title">
                {{ row.title }}
              </td>
              <td class="px-3 py-2 text-text-muted" data-testid="scorecard-domain">
                {{ row.domain }}
              </td>
              <td class="px-3 py-2 text-text-muted" data-testid="scorecard-context">
                {{ row.context }}
              </td>
              <td class="px-3 py-2 text-right font-semibold text-text" data-testid="scorecard-score">
                {{ row.scoreText }}
              </td>
              <td class="px-3 py-2" data-testid="scorecard-result">
                <Badge
                  :variant="row.passed ? 'success' : 'danger'"
                  copyable
                  :copy-text="row.passed ? 'PASS' : 'FAIL'"
                >
                  {{ row.passed ? 'PASS' : 'FAIL' }}
                </Badge>
              </td>
              <td class="px-3 py-2 text-text-muted" data-testid="scorecard-message">
                {{ row.message }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>
  </section>
</template>
