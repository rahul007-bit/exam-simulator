import { expect, test } from '@playwright/test'

test('candidate route renders the app shell', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('#app')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Candidate Workspace' })).toBeVisible()
})

test('admin route renders the app shell', async ({ page }) => {
  await page.goto('/admin')
  await expect(page.locator('#app')).toBeVisible()
})
