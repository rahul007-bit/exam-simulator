import type { ScorecardRow, SubmitResponse } from '@/api/actions'

/**
 * Scorecard view model (FE-024) for the final report returned by
 * `POST /api/action/submit` (see `SubmitResponse.scorecard[]`).
 *
 * The mapping keeps the exact payload fields required by the task acceptance
 * criteria — `task_num, id, title, domain, context, score, max_score, passed,
 * message` — and adds a preformatted `scoreText` for display. Kept in a plain
 * `.ts` module so the row mapping is unit-testable without mounting the SFC.
 */

export interface ScorecardRowView {
  task_num: number
  id: string
  title: string
  domain: string
  context: string
  score: number
  max_score: number
  passed: boolean
  message: string
  scoreText: string
}

export interface ScorecardSummary {
  percentage: number
  totalEarned: number
  totalPossible: number
  passed: boolean
  threshold: number
  examName: string
  sessionId: string
  submittedAt: string
}

export function scorecardRows(result: SubmitResponse | null | undefined): ScorecardRowView[] {
  const rows = result?.scorecard ?? []
  return rows.map((row: ScorecardRow) => ({
    task_num: row.task_num,
    id: row.id,
    title: row.title,
    domain: row.domain,
    context: row.context,
    score: row.score,
    max_score: row.max_score,
    passed: row.passed,
    message: row.message,
    scoreText: `${row.score}/${row.max_score}`,
  }))
}

export function scorecardSummary(result: SubmitResponse | null | undefined): ScorecardSummary {
  return {
    percentage: result?.percentage ?? 0,
    totalEarned: result?.total_earned ?? 0,
    totalPossible: result?.total_possible ?? 0,
    passed: result?.passed ?? false,
    threshold: result?.threshold ?? 0,
    examName: result?.exam_name ?? '',
    sessionId: result?.session_id ?? '',
    submittedAt: result?.submitted_at ?? '',
  }
}
