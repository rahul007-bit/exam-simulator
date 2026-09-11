import { expect, test } from '@playwright/test'

import { INACTIVE_SESSION, mockApi, stubBrowserApis } from './helpers'

/**
 * Per-session owner lock UI.
 *
 * When another window/device owns the active exam the backend answers
 * `GET /api/session` with a normal (HTTP 200) inactive payload carrying
 * `locked: true`. The candidate must see the locked card instead of the start
 * screen, and Retry must re-fetch the session so it can recover once the other
 * client releases the lock.
 */

const LOCKED_SESSION = {
  active: false,
  session: null,
  locked: true,
  locked_preset: null,
  is_admin: false,
}

test.describe('per-session owner lock', () => {
  test('shows the locked screen and Retry re-fetches into the start screen', async ({ page }) => {
    await stubBrowserApis(page)

    let sessionCalls = 0
    await mockApi(page, [
      {
        path: '/api/session',
        // First fetch: owned elsewhere. Every fetch after Retry: released.
        body: () => {
          sessionCalls += 1
          return sessionCalls === 1 ? LOCKED_SESSION : INACTIVE_SESSION
        },
      },
      { path: '/api/timer', body: { active: false } },
      { path: '/api/presets', body: { presets: [], selected: null } },
    ])

    await page.goto('/')

    // Locked card wins over both the start screen and the workspace.
    await expect(page.getByTestId('session-locked')).toBeVisible()
    await expect(page.getByTestId('start-exam')).toBeHidden()
    await expect(page.getByTestId('candidate-workspace')).toBeHidden()

    await page.getByTestId('session-locked-retry').click()

    // Retry re-fetched /api/session; the released payload renders the start screen.
    await expect(page.getByTestId('session-locked')).toBeHidden()
    await expect(page.getByTestId('start-exam')).toBeVisible()
    expect(sessionCalls).toBeGreaterThanOrEqual(2)
  })
})
