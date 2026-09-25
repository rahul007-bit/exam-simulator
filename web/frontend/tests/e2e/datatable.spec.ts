import { expect, test } from '@playwright/test'

/**
 * FE-013 browser coverage for the admin DataTable demo on `/dev/ui`.
 *
 * T2 from `tasks.json`: clicking a column header reorders the rows and
 * filtering to no match shows the empty state. The header sort is also
 * exercised from the keyboard because the sort control is a real button.
 */
test.describe('FE-013 DataTable (admin)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dev/ui')
    await expect(page.getByTestId('datatable-demo')).toBeVisible()
  })

  test('T2: clicking a header sorts the rows and updates aria-sort', async ({ page }) => {
    const table = page.getByTestId('datatable-demo')
    const firstSession = table.locator('[data-testid="datatable-cell-id"]').first()
    await expect(firstSession).toHaveText('S-1001')

    const sessionHeader = table.getByTestId('datatable-sort').filter({ hasText: 'Session' })
    await sessionHeader.click()
    await expect(table.locator('th', { hasText: 'Session' })).toHaveAttribute(
      'aria-sort',
      'ascending',
    )

    // enableSortingRemoval is disabled, so the second toggle sorts descending.
    await sessionHeader.click()
    await expect(table.locator('th', { hasText: 'Session' })).toHaveAttribute(
      'aria-sort',
      'descending',
    )
    await expect(firstSession).toHaveText('S-1012')
  })

  test('T2: filtering to no match shows the empty state', async ({ page }) => {
    const table = page.getByTestId('datatable-demo')
    const search = table.locator('[data-testid="datatable-search"] input')

    await search.fill('CKA')
    await expect(table.locator('[data-testid="datatable-row"]')).not.toHaveCount(0)

    await search.fill('zzz-no-such-session')
    await expect(table.getByTestId('datatable-empty')).toBeVisible()
    await expect(table.getByTestId('datatable-empty')).toContainText('No rows to display')
    await expect(table.locator('[data-testid="datatable-row"]')).toHaveCount(0)
  })

  test('the sort control is keyboard operable', async ({ page }) => {
    const table = page.getByTestId('datatable-demo')
    const sessionHeader = table.getByTestId('datatable-sort').filter({ hasText: 'Session' })

    await sessionHeader.focus()
    await page.keyboard.press('Enter')
    await page.keyboard.press('Enter')
    await expect(table.locator('th', { hasText: 'Session' })).toHaveAttribute(
      'aria-sort',
      'descending',
    )
  })

  test('rows expose pagination and focusable rows in the demo', async ({ page }) => {
    const table = page.getByTestId('datatable-demo')
    await expect(table.getByTestId('datatable-page')).toContainText('Page 1 of 3')
    await expect(table.locator('[data-testid="datatable-row"]').first()).toHaveAttribute(
      'tabindex',
      '0',
    )

    await table.getByTestId('datatable-next').click()
    await expect(table.getByTestId('datatable-page')).toContainText('Page 2 of 3')
  })
})
