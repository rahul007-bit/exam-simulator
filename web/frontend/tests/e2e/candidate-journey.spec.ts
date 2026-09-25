import { expect, test } from '@playwright/test'

import { mockCandidateBackend } from './helpers'

/**
 * FE-042 T1 — candidate critical path.
 *
 * The whole journey runs against mocked `/api/**` fixtures (see `helpers.ts`);
 * there is no live backend. It covers the start screen, starting an exam,
 * rendering the workspace + header, the task footer Previous/Next controls,
 * navigating to another task through the question-drawer navigator (including
 * the reopen/refetch parity fix), and reaching the submit scorecard.
 */
test.describe('FE-042 candidate journey', () => {
  test.beforeEach(async ({ page }) => {
    await mockCandidateBackend(page)
  })

  test('T1: starts an exam, navigates tasks and renders the submit scorecard', async ({
    page,
  }) => {
    await page.goto('/')

    // Start screen (inactive session). FS-008: the preset catalog is admin-only,
    // so a non-admin candidate sees only Start.
    await expect(page.getByTestId('start-exam')).toBeVisible()
    await expect(page.getByTestId('choose-preset')).toHaveCount(0)
    await expect(page.getByRole('heading', { name: 'Kubernetes Exam Simulator' })).toBeVisible()

    await page.getByTestId('start-exam').click()

    // Workspace + header render for the active session.
    await expect(page.getByTestId('candidate-workspace')).toBeVisible()
    await expect(page.getByTestId('candidate-header')).toBeVisible()
    await expect(page.getByTestId('header-exam-name')).toHaveText('Mock Preset')
    await expect(page.getByTestId('header-progress')).toContainText('Task 1 of 2')
    await expect(page.getByTestId('header-timer')).toBeVisible()

    // Task footer: at the first task only Next is enabled.
    await expect(page.getByTestId('task-footer')).toBeVisible()
    await expect(page.getByTestId('task-progress-text')).toHaveText('Task 1 of 2')
    await expect(page.getByTestId('task-prev')).toBeDisabled()
    await expect(page.getByTestId('task-next')).toBeEnabled()

    // Next -> Task 2 (footer + header stay in sync; Next now disabled).
    await page.getByTestId('task-next').click()
    await expect(page.getByTestId('header-progress')).toContainText('Task 2 of 2')
    await expect(page.getByTestId('task-progress-text')).toHaveText('Task 2 of 2')
    await expect(page.getByTestId('task-next')).toBeDisabled()
    await expect(page.getByTestId('task-prev')).toBeEnabled()
    await expect(page.getByRole('heading', { level: 1, name: 'Task Two' })).toBeVisible()

    // Previous -> back to Task 1.
    await page.getByTestId('task-prev').click()
    await expect(page.getByTestId('header-progress')).toContainText('Task 1 of 2')
    await expect(page.getByTestId('task-progress-text')).toHaveText('Task 1 of 2')

    // Question drawer / navigator -> jump to the second task.
    await page.getByTestId('header-progress').click()
    await expect(page.getByTestId('question-nav-grid')).toBeVisible()
    await expect(page.getByTestId('question-nav-item')).toHaveCount(2)

    await page.getByTestId('question-nav-item').filter({ hasText: 'Task Two' }).click()

    await expect(page.getByTestId('question-nav-grid')).toBeHidden()
    await expect(page.getByTestId('header-progress')).toContainText('Task 2 of 2')
    await expect(page.getByRole('heading', { level: 1, name: 'Task Two' })).toBeVisible()

    // Reopen the drawer: the refetch must mark the newly-opened task current.
    await page.getByTestId('header-progress').click()
    await expect(page.getByTestId('question-nav-grid')).toBeVisible()
    const currentItem = page.locator('[data-testid="question-nav-item"][data-state="current"]')
    await expect(currentItem).toHaveCount(1)
    await expect(currentItem).toContainText('Task Two')
    await page.getByRole('button', { name: 'Close' }).click()
    await expect(page.getByTestId('question-nav-grid')).toBeHidden()

    // Submit -> confirm -> scorecard.
    await page.getByTestId('header-submit').click()
    await expect(page.getByTestId('dialog-panel')).toBeVisible()
    await page.getByTestId('confirm').click()

    const scorecard = page.getByTestId('scorecard')
    await expect(scorecard).toBeVisible()
    await expect(page.getByTestId('scorecard-percentage')).toHaveText('50%')
    await expect(scorecard.getByTestId('scorecard-table')).toContainText('Task One')
  })
})
