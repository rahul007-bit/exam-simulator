import { expect, test } from '@playwright/test'

import { mockAdminBackend } from './helpers'

/**
 * FE-042 T1 — admin critical path.
 *
 * Authenticated admin (`/api/admin/check`) exercises both surfaces against
 * mocked fixtures: `/admin` (sessions table + row-action dialog) and
 * `/admin/settings` (default-preset, server-resource and create-invite forms).
 * No live backend is required.
 */
test.describe('FE-042 admin journey', () => {
  test.beforeEach(async ({ page }) => {
    await mockAdminBackend(page)
  })

  test('T1: lists sessions, runs row actions and settings invite flow', async ({ page }) => {
    await page.goto('/admin')

    // Sessions surface.
    await expect(page.getByRole('heading', { name: 'Admin plane' })).toBeVisible()
    const row = page.getByTestId('datatable-row').first()
    await expect(row).toContainText('Mock Exam')

    // Row action dialog -> terminate -> confirm.
    await row.click()
    await expect(page.getByTestId('session-action-terminate')).toBeVisible()
    await expect(page.getByTestId('session-action-reset')).toBeVisible()
    await expect(page.getByTestId('session-action-end')).toBeVisible()

    await page.getByTestId('session-action-terminate').click()
    await expect(page.getByTestId('dialog-panel')).toBeVisible()
    await page.getByTestId('confirm').click()

    await expect(
      page.locator('.toast').filter({ hasText: 'Terminated sess-admin-1' }),
    ).toBeVisible()

    // Navigate to the settings page.
    await page.getByTestId('admin-settings-link').click()
    await expect(page).toHaveURL(/\/admin\/settings$/)
    await expect(page.getByRole('heading', { name: 'Default preset' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Server resources' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Create candidate invite' })).toBeVisible()
    await expect(page.getByTestId('config-save')).toBeVisible()
    await expect(page.getByTestId('resources-max-input')).toBeVisible()
    await expect(page.getByTestId('resources-save')).toBeVisible()

    // Create-invite flow.
    await page.getByTestId('invite-generate').click()
    await expect(page.getByTestId('invite-output')).toBeVisible()
    await expect(page.getByTestId('invite-url')).toContainText('token=invite-token-1')
  })
})
