import { expect, test } from '@playwright/test'

import { mockAdminBackend, mockCandidateBackend } from './helpers'

test('candidate route renders the app shell', async ({ page }) => {
  await mockCandidateBackend(page)
  await page.goto('/')
  await expect(page.locator('#app')).toBeVisible()
  await expect(page.getByTestId('app-shell')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Kubernetes Exam Simulator' })).toBeVisible()
  await expect(page.getByTestId('start-exam')).toBeVisible()
})

test('admin route renders the app shell', async ({ page }) => {
  await mockAdminBackend(page)
  await page.goto('/admin')
  await expect(page.locator('#app')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Admin plane' })).toBeVisible()
})
