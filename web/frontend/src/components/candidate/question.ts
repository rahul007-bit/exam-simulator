import { apiRequest } from '@/api/client'
import type { BadgeVariant } from '@/components/ui'

/**
 * Candidate question-navigator model + state mapping (FE-024).
 *
 * Kept in a plain `.ts` module (like FE-022 `task.ts`) because the ambient
 * `*.vue` declaration types SFCs as opaque components that cannot carry named
 * type exports, and because the state machine is worth unit-testing on its own.
 *
 * State precedence mirrors the legacy drawer (`web/static/js/app.js:1456`):
 * current → flagged → scored → pending. A scored task never reveals pass/fail
 * during the exam; it only means the task has been evaluated.
 */

export interface QuestionScoreData {
  passed: boolean
  score: number
  max_score: number
  message: string
}

/** One row from `GET /api/questions` (see `web/server.py:487`). */
export interface QuestionNavItem {
  task_num: number
  id: string
  title: string
  domain?: string
  points?: number
  target_context?: string | null
  namespace?: string | null
  is_current?: boolean
  is_flagged?: boolean
  score_data?: QuestionScoreData | null
}

export type NavState = 'current' | 'flagged' | 'scored' | 'pending'

export interface NavSummary {
  total: number
  current: number
  flagged: number
  scored: number
  pending: number
}

const NAV_LABELS: Record<NavState, string> = {
  current: 'Current',
  flagged: 'Flagged',
  scored: 'Scored',
  pending: 'Pending',
}

const NAV_VARIANTS: Record<NavState, BadgeVariant> = {
  current: 'accent',
  flagged: 'warning',
  scored: 'info',
  pending: 'neutral',
}

/** Resolve the single displayed state for a task, in legacy precedence order. */
export function navState(item: QuestionNavItem): NavState {
  if (item.is_current) return 'current'
  if (item.is_flagged) return 'flagged'
  if (item.score_data) return 'scored'
  return 'pending'
}

export function navStateLabel(state: NavState): string {
  return NAV_LABELS[state]
}

export function navStateVariant(state: NavState): BadgeVariant {
  return NAV_VARIANTS[state]
}

export function navSummary(items: QuestionNavItem[]): NavSummary {
  const summary: NavSummary = { total: items.length, current: 0, flagged: 0, scored: 0, pending: 0 }
  for (const item of items) summary[navState(item)] += 1
  return summary
}

export interface QuestionsResponse {
  questions: QuestionNavItem[]
  total?: number
}

/** Load the navigator rows. Existing typed client (read-only import). */
export async function fetchQuestions(signal?: AbortSignal): Promise<QuestionNavItem[]> {
  const response = await apiRequest<QuestionsResponse>('/api/questions', { signal })
  return response.questions ?? []
}
