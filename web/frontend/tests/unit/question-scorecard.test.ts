import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { SubmitResponse } from '@/api/actions'
import ExamScorecard from '@/components/candidate/ExamScorecard.vue'
import { scorecardRows, scorecardSummary } from '@/components/candidate/scorecard'

/**
 * FE-024 unit coverage for the final scorecard: the row mapping must preserve
 * the `POST /api/action/submit` payload fields exactly and the component must
 * render the submitted rows.
 */

const RESULT: SubmitResponse = {
  scorecard: [
    {
      task_num: 1,
      id: 'q1',
      title: 'Create a pod',
      domain: 'Workloads',
      difficulty: 'easy',
      context: 'k3d-cka',
      score: 5,
      max_score: 5,
      passed: true,
      message: 'All good',
    },
    {
      task_num: 2,
      id: 'q2',
      title: 'Expose a service',
      domain: 'Networking',
      difficulty: 'medium',
      context: 'k3d-cka',
      score: 2,
      max_score: 5,
      passed: false,
      message: 'Missing selector',
    },
  ],
  total_earned: 7,
  total_possible: 10,
  percentage: 70,
  passed: true,
  threshold: 66,
  session_id: 'sess-1',
  exam_name: 'Mock 1',
  submitted_at: '2026-09-10T00:00:00Z',
}

describe('scorecard row mapping — FE-024', () => {
  it('preserves every submit-payload field and formats the score', () => {
    const rows = scorecardRows(RESULT)
    expect(rows).toHaveLength(2)

    expect(rows[0]).toEqual({
      task_num: 1,
      id: 'q1',
      title: 'Create a pod',
      domain: 'Workloads',
      context: 'k3d-cka',
      score: 5,
      max_score: 5,
      passed: true,
      message: 'All good',
      scoreText: '5/5',
    })
    expect(rows[1].scoreText).toBe('2/5')
    expect(rows[1].passed).toBe(false)
  })

  it('returns no rows for a null result', () => {
    expect(scorecardRows(null)).toEqual([])
    expect(scorecardRows(undefined)).toEqual([])
  })

  it('exposes the summary totals', () => {
    expect(scorecardSummary(RESULT)).toMatchObject({
      percentage: 70,
      totalEarned: 7,
      totalPossible: 10,
      passed: true,
      threshold: 66,
    })
  })
})

describe('ExamScorecard — FE-024', () => {
  it('renders the summary matching the payload', () => {
    const wrapper = mount(ExamScorecard, { props: { result: RESULT } })
    expect(wrapper.get('[data-testid="scorecard-percentage"]').text()).toBe('70%')
    expect(wrapper.get('[data-testid="scorecard-totals"]').text()).toBe('7 / 10 points earned')
    expect(wrapper.get('[data-testid="scorecard-summary"]').text()).toContain('PASSED')
    expect(wrapper.get('[data-testid="scorecard-summary"]').text()).toContain('66%')
  })

  it('renders one row per scorecard entry with the expected cells', () => {
    const wrapper = mount(ExamScorecard, { props: { result: RESULT } })
    const rows = wrapper.findAll('[data-testid="scorecard-row"]')
    expect(rows).toHaveLength(2)

    const first = rows[0]
    expect(first.get('[data-testid="scorecard-id"]').text()).toBe('q1')
    expect(first.get('[data-testid="scorecard-title"]').text()).toBe('Create a pod')
    expect(first.get('[data-testid="scorecard-domain"]').text()).toBe('Workloads')
    expect(first.get('[data-testid="scorecard-context"]').text()).toBe('k3d-cka')
    expect(first.get('[data-testid="scorecard-score"]').text()).toBe('5/5')
    expect(first.get('[data-testid="scorecard-result"]').text()).toBe('PASS')
    expect(first.get('[data-testid="scorecard-message"]').text()).toBe('All good')

    const second = rows[1]
    expect(second.get('[data-testid="scorecard-score"]').text()).toBe('2/5')
    expect(second.get('[data-testid="scorecard-result"]').text()).toBe('FAIL')
    expect(second.get('[data-testid="scorecard-message"]').text()).toBe('Missing selector')
  })

  it('renders an empty state for a null result', () => {
    const wrapper = mount(ExamScorecard, { props: { result: null } })
    expect(wrapper.findAll('[data-testid="scorecard-row"]')).toHaveLength(0)
    expect(wrapper.text()).toContain('No submissions to display.')
  })
})
